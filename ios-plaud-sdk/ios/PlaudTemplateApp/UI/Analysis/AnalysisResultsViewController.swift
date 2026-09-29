import UIKit

/// Displays CareCompass analysis results: engagement timeline, quality scores, and coaching insights
final class AnalysisResultsViewController: UIViewController {
    
    // MARK: - Properties
    
    private let session: SessionResponse
    
    // MARK: - Views
    
    private let scrollView = UIScrollView()
    private let contentStack = UIStackView()
    
    // Quality Score Card
    private let qualityCard = UIView()
    private let qualityScoreLabel = UILabel()
    private let qualityTitleLabel = UILabel()
    
    // Dimension Scores
    private let dimensionsStack = UIStackView()
    
    // Engagement Timeline
    private let timelineCard = UIView()
    private let timelineTitleLabel = UILabel()
    private let timelineStack = UIStackView()
    
    // Coaching Insights
    private let coachingCard = UIView()
    private let coachingTitleLabel = UILabel()
    private let coachingStack = UIStackView()
    
    // MARK: - Init
    
    init(session: SessionResponse) {
        self.session = session
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) { fatalError() }
    
    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor.systemGroupedBackground
        title = "Analysis Results"
        setupNavBar()
        setupLayout()
        populateData()
    }
    
    // MARK: - Setup
    
    private func setupNavBar() {
        let closeBtn = UIBarButtonItem(
            barButtonSystemItem: .close,
            target: self,
            action: #selector(closeTapped)
        )
        navigationItem.rightBarButtonItem = closeBtn
    }
    
    private func setupLayout() {
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.alwaysBounceVertical = true
        view.addSubview(scrollView)
        
        contentStack.axis = .vertical
        contentStack.spacing = 20
        contentStack.translatesAutoresizingMaskIntoConstraints = false
        scrollView.addSubview(contentStack)
        
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            
            contentStack.topAnchor.constraint(equalTo: scrollView.topAnchor, constant: 20),
            contentStack.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor, constant: -20),
            contentStack.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor, constant: 16),
            contentStack.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor, constant: -16),
            contentStack.widthAnchor.constraint(equalTo: scrollView.widthAnchor, constant: -32),
        ])
        
        setupQualityCard()
        setupTimelineCard()
        setupCoachingCard()
        
        contentStack.addArrangedSubview(qualityCard)
        contentStack.addArrangedSubview(timelineCard)
        contentStack.addArrangedSubview(coachingCard)
    }
    
    private func setupQualityCard() {
        qualityCard.backgroundColor = .white
        qualityCard.layer.cornerRadius = 16
        qualityCard.translatesAutoresizingMaskIntoConstraints = false
        
        qualityTitleLabel.text = "Conversation Quality"
        qualityTitleLabel.font = .systemFont(ofSize: 13, weight: .medium)
        qualityTitleLabel.textColor = .secondaryLabel
        qualityTitleLabel.translatesAutoresizingMaskIntoConstraints = false
        
        qualityScoreLabel.font = .systemFont(ofSize: 64, weight: .light)
        qualityScoreLabel.textColor = .label
        qualityScoreLabel.textAlignment = .center
        qualityScoreLabel.translatesAutoresizingMaskIntoConstraints = false
        
        dimensionsStack.axis = .horizontal
        dimensionsStack.distribution = .fillEqually
        dimensionsStack.spacing = 8
        dimensionsStack.translatesAutoresizingMaskIntoConstraints = false
        
        qualityCard.addSubview(qualityTitleLabel)
        qualityCard.addSubview(qualityScoreLabel)
        qualityCard.addSubview(dimensionsStack)
        
        NSLayoutConstraint.activate([
            qualityTitleLabel.topAnchor.constraint(equalTo: qualityCard.topAnchor, constant: 16),
            qualityTitleLabel.leadingAnchor.constraint(equalTo: qualityCard.leadingAnchor, constant: 16),
            
            qualityScoreLabel.topAnchor.constraint(equalTo: qualityTitleLabel.bottomAnchor, constant: 8),
            qualityScoreLabel.centerXAnchor.constraint(equalTo: qualityCard.centerXAnchor),
            
            dimensionsStack.topAnchor.constraint(equalTo: qualityScoreLabel.bottomAnchor, constant: 16),
            dimensionsStack.leadingAnchor.constraint(equalTo: qualityCard.leadingAnchor, constant: 16),
            dimensionsStack.trailingAnchor.constraint(equalTo: qualityCard.trailingAnchor, constant: -16),
            dimensionsStack.bottomAnchor.constraint(equalTo: qualityCard.bottomAnchor, constant: -16),
        ])
    }
    
    private func setupTimelineCard() {
        timelineCard.backgroundColor = .white
        timelineCard.layer.cornerRadius = 16
        timelineCard.translatesAutoresizingMaskIntoConstraints = false
        
        timelineTitleLabel.text = "Engagement Timeline"
        timelineTitleLabel.font = .systemFont(ofSize: 13, weight: .medium)
        timelineTitleLabel.textColor = .secondaryLabel
        timelineTitleLabel.translatesAutoresizingMaskIntoConstraints = false
        
        timelineStack.axis = .horizontal
        timelineStack.distribution = .fillEqually
        timelineStack.spacing = 2
        timelineStack.translatesAutoresizingMaskIntoConstraints = false
        
        timelineCard.addSubview(timelineTitleLabel)
        timelineCard.addSubview(timelineStack)
        
        NSLayoutConstraint.activate([
            timelineTitleLabel.topAnchor.constraint(equalTo: timelineCard.topAnchor, constant: 16),
            timelineTitleLabel.leadingAnchor.constraint(equalTo: timelineCard.leadingAnchor, constant: 16),
            
            timelineStack.topAnchor.constraint(equalTo: timelineTitleLabel.bottomAnchor, constant: 12),
            timelineStack.leadingAnchor.constraint(equalTo: timelineCard.leadingAnchor, constant: 16),
            timelineStack.trailingAnchor.constraint(equalTo: timelineCard.trailingAnchor, constant: -16),
            timelineStack.heightAnchor.constraint(equalToConstant: 40),
            timelineStack.bottomAnchor.constraint(equalTo: timelineCard.bottomAnchor, constant: -16),
        ])
    }
    
    private func setupCoachingCard() {
        coachingCard.backgroundColor = .white
        coachingCard.layer.cornerRadius = 16
        coachingCard.translatesAutoresizingMaskIntoConstraints = false
        
        coachingTitleLabel.text = "Coaching Insights"
        coachingTitleLabel.font = .systemFont(ofSize: 13, weight: .medium)
        coachingTitleLabel.textColor = .secondaryLabel
        coachingTitleLabel.translatesAutoresizingMaskIntoConstraints = false
        
        coachingStack.axis = .vertical
        coachingStack.spacing = 16
        coachingStack.translatesAutoresizingMaskIntoConstraints = false
        
        coachingCard.addSubview(coachingTitleLabel)
        coachingCard.addSubview(coachingStack)
        
        NSLayoutConstraint.activate([
            coachingTitleLabel.topAnchor.constraint(equalTo: coachingCard.topAnchor, constant: 16),
            coachingTitleLabel.leadingAnchor.constraint(equalTo: coachingCard.leadingAnchor, constant: 16),
            
            coachingStack.topAnchor.constraint(equalTo: coachingTitleLabel.bottomAnchor, constant: 12),
            coachingStack.leadingAnchor.constraint(equalTo: coachingCard.leadingAnchor, constant: 16),
            coachingStack.trailingAnchor.constraint(equalTo: coachingCard.trailingAnchor, constant: -16),
            coachingStack.bottomAnchor.constraint(equalTo: coachingCard.bottomAnchor, constant: -16),
        ])
    }
    
    // MARK: - Data Population
    
    private func populateData() {
        // Quality Score
        if let quality = session.conversationQuality {
            qualityScoreLabel.text = String(format: "%.0f", quality.qualityIndex)
            
            // Add dimension scores
            let dimensions = [
                ("Clarity", quality.clarity),
                ("Authority", quality.authority),
                ("Energy", quality.energy),
                ("Rapport", quality.rapport),
                ("Learning", quality.learning),
            ]
            
            for (name, score) in dimensions {
                let view = createDimensionView(name: name, score: score)
                dimensionsStack.addArrangedSubview(view)
            }
        } else {
            qualityScoreLabel.text = "--"
        }
        
        // Engagement Timeline
        if let windows = session.engagementWindows {
            for window in windows {
                let bar = UIView()
                bar.layer.cornerRadius = 4
                
                switch window.engagementStatus {
                case "engaged":
                    bar.backgroundColor = UIColor.systemGreen
                case "neutral":
                    bar.backgroundColor = UIColor.systemYellow
                case "disengaged":
                    bar.backgroundColor = UIColor.systemRed
                default:
                    bar.backgroundColor = UIColor.systemGray
                }
                
                timelineStack.addArrangedSubview(bar)
            }
        }
        
        // Coaching Insights
        if let insights = session.coachingInsights {
            for insight in insights {
                let view = createCoachingInsightView(insight: insight)
                coachingStack.addArrangedSubview(view)
            }
        } else {
            let emptyLabel = UILabel()
            emptyLabel.text = "No coaching insights available"
            emptyLabel.textColor = .secondaryLabel
            emptyLabel.font = .systemFont(ofSize: 14)
            coachingStack.addArrangedSubview(emptyLabel)
        }
    }
    
    private func createDimensionView(name: String, score: Double) -> UIView {
        let container = UIView()
        
        let nameLabel = UILabel()
        nameLabel.text = name
        nameLabel.font = .systemFont(ofSize: 11)
        nameLabel.textColor = .secondaryLabel
        nameLabel.textAlignment = .center
        nameLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let scoreLabel = UILabel()
        scoreLabel.text = String(format: "%.0f", score)
        scoreLabel.font = .systemFont(ofSize: 20, weight: .medium)
        scoreLabel.textColor = colorForScore(score)
        scoreLabel.textAlignment = .center
        scoreLabel.translatesAutoresizingMaskIntoConstraints = false
        
        container.addSubview(nameLabel)
        container.addSubview(scoreLabel)
        
        NSLayoutConstraint.activate([
            scoreLabel.topAnchor.constraint(equalTo: container.topAnchor),
            scoreLabel.centerXAnchor.constraint(equalTo: container.centerXAnchor),
            
            nameLabel.topAnchor.constraint(equalTo: scoreLabel.bottomAnchor, constant: 2),
            nameLabel.centerXAnchor.constraint(equalTo: container.centerXAnchor),
            nameLabel.bottomAnchor.constraint(equalTo: container.bottomAnchor),
        ])
        
        return container
    }
    
    private func createCoachingInsightView(insight: CoachingInsightResponse) -> UIView {
        let container = UIView()
        container.backgroundColor = UIColor.systemGray6
        container.layer.cornerRadius = 12
        
        let titleLabel = UILabel()
        titleLabel.text = insight.title
        titleLabel.font = .systemFont(ofSize: 16, weight: .semibold)
        titleLabel.textColor = .label
        titleLabel.numberOfLines = 0
        titleLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let descLabel = UILabel()
        descLabel.text = insight.description
        descLabel.font = .systemFont(ofSize: 14)
        descLabel.textColor = .secondaryLabel
        descLabel.numberOfLines = 0
        descLabel.translatesAutoresizingMaskIntoConstraints = false
        
        let actionLabel = UILabel()
        actionLabel.text = "💡 " + insight.suggestedAction
        actionLabel.font = .systemFont(ofSize: 14, weight: .medium)
        actionLabel.textColor = .systemBlue
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
    
    private func colorForScore(_ score: Double) -> UIColor {
        if score >= 70 {
            return .systemGreen
        } else if score >= 50 {
            return .systemYellow
        } else {
            return .systemRed
        }
    }
    
    // MARK: - Actions
    
    @objc private func closeTapped() {
        dismiss(animated: true)
    }
}
