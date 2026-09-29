import Foundation
import Combine

/// Manages CareCompass backend analysis pipeline
/// Flow: Create session -> Upload audio -> Poll for results
final class AnalysisManager {
    
    static let shared = AnalysisManager()
    
    // MARK: - State
    
    enum AnalysisState: Equatable {
        case idle
        case creatingSession
        case uploading(progress: Double)
        case analyzing(status: String)
        case completed(SessionResponse)
        case failed(String)
        
        static func == (lhs: AnalysisState, rhs: AnalysisState) -> Bool {
            switch (lhs, rhs) {
            case (.idle, .idle): return true
            case (.creatingSession, .creatingSession): return true
            case (.uploading(let p1), .uploading(let p2)): return p1 == p2
            case (.analyzing(let s1), .analyzing(let s2)): return s1 == s2
            case (.completed, .completed): return true
            case (.failed(let e1), .failed(let e2)): return e1 == e2
            default: return false
            }
        }
    }
    
    private let stateSubject = CurrentValueSubject<AnalysisState, Never>(.idle)
    var statePublisher: AnyPublisher<AnalysisState, Never> {
        stateSubject.eraseToAnyPublisher()
    }
    
    private let api = CareCompassAPI.shared
    private var currentFileId: String?
    
    private init() {}
    
    // MARK: - Public API
    
    /// Start analysis for a synced recording
    func analyze(file: RecordingFile, providerId: String = "default-provider") {
        guard file.isSynced else {
            stateSubject.send(.failed("File not synced yet"))
            return
        }
        
        guard let audioPath = RecordingStore.shared.resolveAbsolutePath(for: file) else {
            stateSubject.send(.failed("Audio file not found"))
            return
        }
        
        currentFileId = file.id
        
        Task {
            await runAnalysisPipeline(fileId: file.id, audioPath: audioPath, providerId: providerId)
        }
    }
    
    func reset() {
        stateSubject.send(.idle)
        currentFileId = nil
    }
    
    // MARK: - Pipeline
    
    private func runAnalysisPipeline(fileId: String, audioPath: String, providerId: String) async {
        do {
            // Step 1: Create session
            await MainActor.run {
                self.stateSubject.send(.creatingSession)
            }
            
            let session = try await api.createSession(providerId: providerId)
            RecordingStore.shared.updateCareCompassSession(id: fileId, sessionId: session.id)
            RecordingStore.shared.updateAnalysisStatus(id: fileId, status: "pending")
            
            AppLog.log("[AnalysisManager] Created session: \(session.id)", level: "API")
            
            // Step 2: Upload audio
            await MainActor.run {
                self.stateSubject.send(.uploading(progress: 0))
            }
            
            let audioURL = URL(fileURLWithPath: audioPath)
            let uploadResponse = try await api.uploadAudio(sessionId: session.id, audioURL: audioURL)
            
            AppLog.log("[AnalysisManager] Upload complete: \(uploadResponse.message)", level: "API")
            RecordingStore.shared.updateAnalysisStatus(id: fileId, status: "transcribing")
            
            // Step 3: Poll for completion
            await MainActor.run {
                self.stateSubject.send(.analyzing(status: "Transcribing audio..."))
            }
            
            let result = try await pollForCompletion(sessionId: session.id, fileId: fileId)
            
            // Step 4: Save results
            if let jsonData = try? JSONEncoder().encode(result),
               let jsonStr = String(data: jsonData, encoding: .utf8) {
                RecordingStore.shared.updateAnalysisResults(id: fileId, json: jsonStr)
            }
            
            await MainActor.run {
                self.stateSubject.send(.completed(result))
            }
            
            AppLog.log("[AnalysisManager] Analysis complete for session \(session.id)", level: "API")
            
        } catch {
            AppLog.log("[AnalysisManager] Analysis failed: \(error)", level: "API")
            await MainActor.run {
                self.stateSubject.send(.failed(error.localizedDescription))
            }
        }
    }
    
    private func pollForCompletion(sessionId: String, fileId: String) async throws -> SessionResponse {
        let maxAttempts = 150 // 5 minutes at 2s intervals
        
        for attempt in 0..<maxAttempts {
            try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
            
            let session = try await api.getSession(sessionId: sessionId)
            
            // Update local status
            RecordingStore.shared.updateAnalysisStatus(id: fileId, status: session.status)
            
            // Update UI with current status
            let statusMessage: String
            switch session.status {
            case "transcribing":
                statusMessage = "Transcribing audio..."
            case "analyzing":
                statusMessage = "Analyzing engagement..."
            case "generating_coaching":
                statusMessage = "Generating coaching insights..."
            case "completed":
                return session
            case "failed":
                throw CareCompassError.analysisFailed(session.errorMessage ?? "Unknown error")
            default:
                statusMessage = "Processing..."
            }
            
            await MainActor.run {
                self.stateSubject.send(.analyzing(status: statusMessage))
            }
        }
        
        throw CareCompassError.timeout
    }
}
