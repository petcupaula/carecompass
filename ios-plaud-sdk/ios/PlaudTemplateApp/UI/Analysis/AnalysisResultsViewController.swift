import UIKit
import Combine

/// CareCompass Analysis Results View
/// Shows engagement analysis, conversation quality, and coaching insights
final class AnalysisResultsViewController: UIViewController {
    
    // MARK: - Dependencies
    private var file: RecordingFile
    private let analysisManager = AnalysisManager.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Views
    private let scrollView = UIScrollView()
    private let contentStack = UIStackView()
    
    private let headerLabel: UILabel = {
        let l = UILabel()
        l.text = "CareCompass Analysis"
        l.font = .systemFont(ofSize: 24, weight: .semibold)
        l.textColor = .black
        l.translatesAutoresizingMaskIntoConstraints = false
        return l
    }()
    
    private let statusLabel: UILabel = {
        let l = UILabel()
        l.font = .systemFont(ofSize: 14)
        l.textColor = UIColor(hex: "#757575")
        l.textAlignment = .center
        l.numberOfLines = 0
        l.translatesAutoresizingMaskIntoConstraints = false
        return l
    }()
    
    private let analyzeButton: UIButton = {
        let btn = UIButton(type: .custom)
        btn.setTitle("Analyze with CareCompass", for: .normal)
        btn.setTitleColor(.white, for: .normal)
        btn.titleLabel?.font = .systemFont(ofSize: 16, weight: .semibold)
        btn.backgroundColor = UIColor(hex: "#2563EB") // Blue
        btn.layer.cornerRadius = 12
        btn.translatesAutoresizingMaskIntoConstraints = false
        return btn
    }()
    
    private let activityIndicator: UIActivityIndicatorView = {
        let ai = UIActivityIndicatorView(style: .large)
        ai.hidesWhenStopped = true
        ai.translatesAutoresizingMaskIntoConstraints = false
        return ai
    }()
    
    // Results sections
    private let qualityCard = QualityScoreCard()
    private let engagementCard = EngagementTimelineCard()
    private let coachingCard = CoachingInsightsCard()
    
    init(file: RecordingFile) {
        self.file = file
        super.init(nibName: nil, bundle: nil)
    }
    required init?(coder: NSCoder) { fatalError() }
    
    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white
        setupNavBar()
        setupLayout()
        setupBindings()
        loadExistingResults()
    }
    
    // MARK: - Setup
    
    private func setupNavBar() {
        title = "Analysis"
        let closeBtn = UIBarButtonItem(barButtonSystemItem: .close, target: self, action: #selector(closeTapped))
        navigationItem.leftBarButtonItem = closeBtn
    }
    
    private func setupLayout() {
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.alwaysBounceVertical = true
        view.addSubview(scrollView)
        
        contentStack.axis = .vertical
        contentStack.spacing = 24
        contentStack.translatesAutoresizingMaskIntoConstraints = false
        scrollView.addSubview(contentStack)
        
        // Add views to stack
        contentStack.addArrangedSubview(headerLabel)
        contentStack.addArrangedSubview(statusLabel)
        contentStack.addArrangedSubview(activityIndicator)
        contentStack.addArrangedSubview(analyzeButton)
        contentStack.addArrangedSubview(qualityCard)
        contentStack.addArrangedSubview(engagementCard)
        contentStack.addArrangedSubview(coachingCard)
        
        // Initially hide result cards
        qualityCard.isHidden = true
        engagementCard.isHidden = true
        coachingCard.isHidden = true
        
        analyzeButton.addTarget(self, action: #selector(analyzeTapped), for: .touchUpInside)
        
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            
            contentStack.topAnchor.constraint(equalTo: scrollView.topAnchor, constant: 24),
            contentStack.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor, constant: -24),
            contentStack.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor, constant: 24),
            contentStack.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor, constant: -24),
            contentStack.widthAnchor.constraint(equalTo: scrollView.widthAnchor, constant: -48),
            
            analyzeButton.heightAnchor.constraint(equalToConstant: 48),
        ])
    }
    
    private func setupBindings() {
        analysisManager.statePublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                self?.updateUI(for: state)
            }
            .store(in: &cancellables)
    }
    
    private func loadExistingResults() {
        // Refresh from store
        if let fresh = RecordingStore.shared.allFiles.first(where: { $0.id == file.id }) {
            file = fresh
        }
        
        if let json = file.analysisJSON,
           let data = json.data(using: .utf8),
           let session = try? JSONDecoder().decode(SessionResponse.self, from: data) {
            showResults(session)
        } else if file.analysisStatus == "completed" {
            statusLabel.text = "Analysis complete but results not cached. Tap to re-analyze."
        } else if let status = file.analysisStatus, status != "completed" && status != "failed" {
            statusLabel.text = "Analysis in progress: \(status)"
        } else {
            statusLabel.text = "Analyze this recording to get engagement insights and coaching recommendations."
        }
    }
    
    // MARK: - UI Updates
    
    private func updateUI(for state: AnalysisManager.AnalysisState) {
        switch state {
        case .idle:
            activityIndicator.stopAnimating()
            analyzeButton.isEnabled = true
            analyzeButton.alpha = 1
            
        case .creatingSession:
            statusLabel.text = "Creating session..."
            activityIndicator.startAnimating()
            analyzeButton.isEnabled = false
            analyzeButton.alpha = 0.5
            
        case .uploading(let progress):
            statusLabel.text = "Uploading audio... \(Int(progress * 100))%"
            
        case .analyzing(let status):
            statusLabel.text = status
            
        case .completed(let session):
            activityIndicator.stopAnimating()
            analyzeButton.isHidden = true
            showResults(session)
            
        case .failed(let error):
            activityIndicator.stopAnimating()
            analyzeButton.isEnabled = true
            analyzeButton.alpha = 1
            statusLabel.text = "Analysis failed: \(error)"
            statusLabel.textColor = .systemRed
        }
    }
    
    private func showResults(_ session: SessionResponse) {
        statusLabel.isHidden = true
        analyzeButton.isHidden = true
        
        // Show quality scores
        if let quality = session.conversationQuality {
            qualityCard.configure(with: quality)
            qualityCard.isHidden = false
        }
        
        // Show engagement timeline
        if let windows = session.engagementWindows, !windows.isEmpty {
            engagementCard.configure(with: windows)
            engagementCard.isHidden = false
        }
        
        // Show coaching insights
        if let insights = session.coachingInsights, !insights.isEmpty {
            coachingCard.configure(with: insights)
            coachingCard.isHidden = false
        }
    }
    
    // MARK: - Actions
    
    @objc private func closeTapped() {
        dismiss(animated: true)
    }
    
    @objc private func analyzeTapped() {
        guard file.isSynced else {
            let alert = UIAlertController(
                title: "File Not Synced",
                message: "Please sync this recording first.",
                preferredStyle: .alert
            )
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            present(alert, animated: true)
            return
        }
        
        analysisManager.analyze(file: file)
    }
}

// MARK: - Quality Score Card

final class QualityScoreCard: UIView {
    
    private let titleLabel: UILabel = {
        let l = UILabel()
        l.text = "Conversation Quality"
        l.font = .systemFont(ofSize: 18, weight: .semibold)
        l.textColor = .black
        return l
    }()
    
    private let overallScoreLabel: UILabel = {
        let l = UILabel()
        l.font = .systemFont(ofSize: 48, weight: .bold)
        l.textColor = UIColor(hex: "#2563EB")
        l.textAlignment = .center
        return l
    }()
    
    private let scoresStack = UIStackView()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    required init?(coder: NSCoder) { fatalError() }
    
    private func setupLayout() {
        backgroundColor = UIColor(hex: "#F8FAFC")
        layer.cornerRadius = 12
        
        let stack = UIStackView(arrangedSubviews: [titleLabel, overallScoreLabel, scoresStack])
        stack.axis = .vertical
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)
        
        scoresStack.axis = .vertical
        scoresStack.spacing = 8
        
        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
        ])
    }
    
    func configure(with quality: ConversationQualityResponse) {
        overallScoreLabel.text = "\(Int(quality.qualityIndex))"
        
        scoresStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        
        let scores: [(String, Double)] = [
            ("Clarity", quality.clarity),
            ("Authority", quality.authority),
            ("Energy", quality.energy),
            ("Rapport", quality.rapport),
            ("Learning", quality.learning),
        ]
        
        for (name, value) in scores {
            let row = createScoreRow(name: name, value: value)
            scoresStack.addArrangedSubview(row)
        }
    }
    
    private func createScoreRow(name: String, value: Double) -> UIView {
        let container = UIView()
        
        let nameLabel = UILabel()
        nameLabel.text = name
        nameLabel.font = .systemFont(ofSize: 14)
        nameLabel.textColor = UIColor(hex: "#64748B")
        nameLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let valueLabel = UILabel()
        valueLabel.text = "\(Int(value))"
        valueLabel.font = .systemFont(ofSize: 14, weight: .medium)
        valueLabel.textColor = .black
        valueLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let progressBg = UIView()
        progressBg.backgroundColor = UIColor(hex: "#E2E8F0")
        progressBg.layer.cornerRadius = 4
        progressBg.translatesAutoresizingMaskIntoConstraints = false
        
        let progressFill = UIView()
        progressFill.backgroundColor = UIColor(hex: "#2563EB")
        progressFill.layer.cornerRadius = 4
        progressFill.translatesAutoresizingMaskIntoConstraints = false
        
        container.addSubview(nameLabel)
        container.addSubview(valueLabel)
        container.addSubview(progressBg)
        progressBg.addSubview(progressFill)
        
        NSLayoutConstraint.activate([
            nameLabel.leadingAnchor.constraint(equalTo: container.leadingAnchor),
            nameLabel.centerYAnchor.constraint(equalTo: container.centerYAnchor),
            nameLabel.widthAnchor.constraint(equalToConstant: 80),
            
            progressBg.leadingAnchor.constraint(equalTo: nameLabel.trailingAnchor, constant: 8),
            progressBg.trailingAnchor.constraint(equalTo: valueLabel.leadingAnchor, constant: -8),
            progressBg.centerYAnchor.constraint(equalTo: container.centerYAnchor),
            progressBg.heightAnchor.constraint(equalToConstant: 8),
            
            progressFill.leadingAnchor.constraint(equalTo: progressBg.leadingAnchor),
            progressFill.topAnchor.constraint(equalTo: progressBg.topAnchor),
            progressFill.bottomAnchor.constraint(equalTo: progressBg.bottomAnchor),
            progressFill.widthAnchor.constraint(equalTo: progressBg.widthAnchor, multiplier: CGFloat(value / 100)),
            
            valueLabel.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            valueLabel.centerYAnchor.constraint(equalTo: container.centerYAnchor),
            valueLabel.widthAnchor.constraint(equalToConstant: 30),
            
            container.heightAnchor.constraint(equalToConstant: 24),
        ])
        
        return container
    }
}

// MARK: - Engagement Timeline Card

final class EngagementTimelineCard: UIView {
    
    private let titleLabel: UILabel = {
        let l = UILabel()
        l.text = "Engagement Timeline"
        l.font = .systemFont(ofSize: 18, weight: .semibold)
        l.textColor = .black
        return l
    }()
    
    private let timelineStack = UIStackView()
    private let signalsStack = UIStackView()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    required init?(coder: NSCoder) { fatalError() }
    
    private func setupLayout() {
        backgroundColor = UIColor(hex: "#F8FAFC")
        layer.cornerRadius = 12
        
        let stack = UIStackView(arrangedSubviews: [titleLabel, timelineStack, signalsStack])
        stack.axis = .vertical
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)
        
        timelineStack.axis = .horizontal
        timelineStack.spacing = 2
        timelineStack.distribution = .fillEqually
        
        signalsStack.axis = .vertical
        signalsStack.spacing = 8
        
        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            
            timelineStack.heightAnchor.constraint(equalToConstant: 32),
        ])
    }
    
    func configure(with windows: [EngagementWindowResponse]) {
        timelineStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        signalsStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        
        // Build timeline bars
        for window in windows {
            let bar = UIView()
            bar.layer.cornerRadius = 4
            
            switch window.engagementStatus.lowercased() {
            case "engaged":
                bar.backgroundColor = UIColor(hex: "#22C55E") // Green
            case "neutral":
                bar.backgroundColor = UIColor(hex: "#F59E0B") // Yellow
            case "disengaged":
                bar.backgroundColor = UIColor(hex: "#EF4444") // Red
            default:
                bar.backgroundColor = UIColor(hex: "#94A3B8") // Gray
            }
            
            timelineStack.addArrangedSubview(bar)
        }
        
        // Collect and display unique signals
        var allSignals: [(String, String, Double)] = [] // (type, rationale, time)
        for window in windows {
            for signal in window.signals {
                let rationale = signal.rationale ?? ""
                allSignals.append((signal.type, rationale, signal.start))
            }
        }
        
        // Show up to 5 most interesting signals
        let uniqueSignals = Array(Set(allSignals.map { "\($0.0): \($0.1)" })).prefix(5)
        
        if !uniqueSignals.isEmpty {
            let signalsTitle = UILabel()
            signalsTitle.text = "Detected Signals"
            signalsTitle.font = .systemFont(ofSize: 14, weight: .medium)
            signalsTitle.textColor = UIColor(hex: "#64748B")
            signalsStack.addArrangedSubview(signalsTitle)
            
            for signalText in uniqueSignals {
                let signalLabel = UILabel()
                signalLabel.text = "• \(signalText)"
                signalLabel.font = .systemFont(ofSize: 13)
                signalLabel.textColor = UIColor(hex: "#475569")
                signalLabel.numberOfLines = 0
                signalsStack.addArrangedSubview(signalLabel)
            }
        }
    }
}

// MARK: - Coaching Insights Card

final class CoachingInsightsCard: UIView {
    
    private let titleLabel: UILabel = {
        let l = UILabel()
        l.text = "Coaching Insights"
        l.font = .systemFont(ofSize: 18, weight: .semibold)
        l.textColor = .black
        return l
    }()
    
    private let insightsStack = UIStackView()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayout()
    }
    required init?(coder: NSCoder) { fatalError() }
    
    private func setupLayout() {
        backgroundColor = UIColor(hex: "#F8FAFC")
        layer.cornerRadius = 12
        
        let stack = UIStackView(arrangedSubviews: [titleLabel, insightsStack])
        stack.axis = .vertical
        stack.spacing = 16
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)
        
        insightsStack.axis = .vertical
        insightsStack.spacing = 16
        
        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
        ])
    }
    
    func configure(with insights: [CoachingInsightResponse]) {
        insightsStack.arrangedSubviews.forEach { $0.removeFromSuperview() }
        
        for insight in insights {
            let card = createInsightCard(insight)
            insightsStack.addArrangedSubview(card)
        }
    }
    
    private func createInsightCard(_ insight: CoachingInsightResponse) -> UIView {
        let container = UIView()
        container.backgroundColor = .white
        container.layer.cornerRadius = 8
        
        let titleLabel = UILabel()
        titleLabel.text = insight.title
        titleLabel.font = .systemFont(ofSize: 16, weight: .semibold)
        titleLabel.textColor = .black
        titleLabel.numberOfLines = 0
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let descLabel = UILabel()
        descLabel.text = insight.description
        descLabel.font = .systemFont(ofSize: 14)
        descLabel.textColor = UIColor(hex: "#64748B")
        descLabel.numberOfLines = 0
        descLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let actionLabel = UILabel()
        actionLabel.text = "💡 \(insight.suggestedAction)"
        actionLabel.font = .systemFont(ofSize: 14, weight: .medium)
        actionLabel.textColor = UIColor(hex: "#2563EB")
        actionLabel.numberOfLines = 0
        actionLabel.translatesAutoresizingMaskIntoConstraints = false
        
        container.addSubview(titleLabel)
        container.addSubview(descLabel)
        container.addSubview(actionLabel)
        
        NSLayoutConstraint.activate([
            titleLabel.topAnchor.constraint(equalTo: container.topAnchor, constant: 12),
            titleLabel.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 12),
            titleLabel.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -12),
            
            descLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 8),
            descLabel.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 12),
            descLabel.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -12),
            
            actionLabel.topAnchor.constraint(equalTo: descLabel.bottomAnchor, constant: 12),
            actionLabel.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 12),
            actionLabel.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -12),
            actionLabel.bottomAnchor.constraint(equalTo: container.bottomAnchor, constant: -12),
        ])
        
        return container
    }
}
