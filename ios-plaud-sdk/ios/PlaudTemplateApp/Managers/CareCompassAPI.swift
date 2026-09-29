import Foundation

/// CareCompass backend API client for session analysis
final class CareCompassAPI {
    
    static let shared = CareCompassAPI()
    
    // Configure this to your backend URL
    private let baseURL: String
    
    private init() {
        // Default to localhost for development
        // Change to your deployed backend URL for production
        self.baseURL = ProcessInfo.processInfo.environment["CARECOMPASS_API_URL"] 
            ?? "http://localhost:8000"
    }
    
    // MARK: - Session Management
    
    /// Create a new session for analysis
    func createSession(providerId: String) async throws -> SessionResponse {
        let url = URL(string: "\(baseURL)/sessions/")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["provider_id": providerId]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw CareCompassError.serverError
        }
        
        return try JSONDecoder().decode(SessionResponse.self, from: data)
    }
    
    /// Upload audio file for analysis
    func uploadAudio(sessionId: String, audioURL: URL) async throws -> UploadResponse {
        let url = URL(string: "\(baseURL)/sessions/\(sessionId)/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // Add file
        let audioData = try Data(contentsOf: audioURL)
        let filename = audioURL.lastPathComponent
        
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/mpeg\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 202 else {
            throw CareCompassError.uploadFailed
        }
        
        return try JSONDecoder().decode(UploadResponse.self, from: data)
    }
    
    /// Get session details including analysis results
    func getSession(sessionId: String) async throws -> SessionResponse {
        let url = URL(string: "\(baseURL)/sessions/\(sessionId)")!
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw CareCompassError.serverError
        }
        
        return try JSONDecoder().decode(SessionResponse.self, from: data)
    }
    
    /// Poll for analysis completion
    func waitForAnalysis(sessionId: String, timeout: TimeInterval = 300) async throws -> SessionResponse {
        let startTime = Date()
        
        while Date().timeIntervalSince(startTime) < timeout {
            let session = try await getSession(sessionId: sessionId)
            
            switch session.status {
            case "completed":
                return session
            case "failed":
                throw CareCompassError.analysisFailed(session.errorMessage ?? "Unknown error")
            default:
                // Still processing, wait and retry
                try await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
            }
        }
        
        throw CareCompassError.timeout
    }
}

// MARK: - Response Models

struct SessionResponse: Codable {
    let id: String
    let providerId: String
    let createdAt: String
    let status: String
    let durationSeconds: Double?
    let transcript: [TranscriptSegmentResponse]?
    let engagementWindows: [EngagementWindowResponse]?
    let conversationQuality: ConversationQualityResponse?
    let coachingInsights: [CoachingInsightResponse]?
    let errorMessage: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case providerId = "provider_id"
        case createdAt = "created_at"
        case status
        case durationSeconds = "duration_seconds"
        case transcript
        case engagementWindows = "engagement_windows"
        case conversationQuality = "conversation_quality"
        case coachingInsights = "coaching_insights"
        case errorMessage = "error_message"
    }
}

struct TranscriptSegmentResponse: Codable {
    let speakerId: String?
    let start: Double
    let end: Double
    let text: String
    
    enum CodingKeys: String, CodingKey {
        case speakerId = "speaker_id"
        case start, end, text
    }
}

struct EngagementWindowResponse: Codable {
    let index: Int
    let startSeconds: Double
    let endSeconds: Double
    let engagementStatus: String
    let signals: [SignalResponse]
    
    enum CodingKeys: String, CodingKey {
        case index
        case startSeconds = "start_seconds"
        case endSeconds = "end_seconds"
        case engagementStatus = "engagement_status"
        case signals
    }
}

struct SignalResponse: Codable {
    let type: String
    let start: Double
    let end: Double
    let probability: String?
    let rationale: String?
    let modality: [String]
}

struct ConversationQualityResponse: Codable {
    let qualityIndex: Double
    let clarity: Double
    let authority: Double
    let energy: Double
    let rapport: Double
    let learning: Double
    
    enum CodingKeys: String, CodingKey {
        case qualityIndex = "quality_index"
        case clarity, authority, energy, rapport, learning
    }
}

struct CoachingInsightResponse: Codable {
    let title: String
    let description: String
    let specificMoment: String?
    let suggestedAction: String
    
    enum CodingKeys: String, CodingKey {
        case title, description
        case specificMoment = "specific_moment"
        case suggestedAction = "suggested_action"
    }
}

struct UploadResponse: Codable {
    let message: String
    let sessionId: String
    
    enum CodingKeys: String, CodingKey {
        case message
        case sessionId = "session_id"
    }
}

// MARK: - Errors

enum CareCompassError: LocalizedError {
    case serverError
    case uploadFailed
    case analysisFailed(String)
    case timeout
    
    var errorDescription: String? {
        switch self {
        case .serverError:
            return "Server error occurred"
        case .uploadFailed:
            return "Failed to upload audio file"
        case .analysisFailed(let message):
            return "Analysis failed: \(message)"
        case .timeout:
            return "Analysis timed out"
        }
    }
}
