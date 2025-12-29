"""SendGrid email service for sending reports."""

import logging
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from config.settings import settings

logger = logging.getLogger(__name__)


def sentiment_score_to_label(score: float) -> str:
    """Convert sentiment score to readable label.
    
    More sensitive thresholds to show more variation.
    
    Args:
        score: Sentiment score (-1.0 to 1.0)
        
    Returns:
        Sentiment label string
    """
    if score >= 0.3:
        return "Very Positive"
    elif score >= 0.1:
        return "Positive"
    elif score >= 0.02:
        return "Slightly Positive"
    elif score <= -0.3:
        return "Very Negative"
    elif score <= -0.1:
        return "Negative"
    elif score <= -0.02:
        return "Slightly Negative"
    else:
        return "Neutral"


class EmailService:
    """Service for sending emails via SendGrid."""

    def __init__(self, api_key: str | None = None):
        """Initialize email service.

        Args:
            api_key: SendGrid API key. If None, uses settings.SENDGRID_API_KEY.
        """
        self.api_key = api_key or settings.SENDGRID_API_KEY
        self.client = SendGridAPIClient(self.api_key)

    def send_report(self, user_email: str, report_data: dict[str, Any]) -> bool:
        """Send portfolio sentiment report email.

        Args:
            user_email: Recipient email address.
            report_data: Report data dictionary containing:
                - portfolio: dict of {ticker: weight}
                - ticker_data: dict of {ticker: {sentiment, summary, risk_level, articles}}
                - portfolio_risk: overall risk level
                - date: report date

        Returns:
            True if email sent successfully, False otherwise.
        """
        try:
            # Generate HTML and plain text content
            html_content = self._generate_html_email(report_data)
            plain_text_content = self._generate_plain_text_email(report_data)

            # Create email
            message = Mail(
                from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
                to_emails=To(user_email),
                subject=f"Portfolio Sentiment Report - {report_data.get('date', 'Today')}",
                plain_text_content=Content("text/plain", plain_text_content),
                html_content=Content("text/html", html_content),
            )

            # Send email
            response = self.client.send(message)

            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully to {user_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"Error sending email to {user_email}: {e}")
            return False

    def _generate_html_email(self, report_data: dict[str, Any]) -> str:
        """Generate HTML email content."""
        portfolio = report_data.get("portfolio", {})
        ticker_data = report_data.get("ticker_data", {})
        portfolio_risk = report_data.get("portfolio_risk", "medium")
        date = report_data.get("date", "Today")

        # Risk color mapping
        risk_colors = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#dc3545",
        }
        risk_color = risk_colors.get(portfolio_risk.lower(), "#6c757d")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .risk-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; 
                              color: white; font-weight: bold; background-color: {risk_color}; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                .sentiment-positive {{ color: #28a745; font-weight: bold; }}
                .sentiment-neutral {{ color: #6c757d; }}
                .sentiment-negative {{ color: #dc3545; font-weight: bold; }}
                .risk-low {{ color: #28a745; font-weight: bold; }}
                .risk-medium {{ color: #ffc107; font-weight: bold; }}
                .risk-high {{ color: #dc3545; font-weight: bold; }}
                .article-link {{ color: #007bff; text-decoration: none; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; 
                           font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Portfolio Sentiment Report</h1>
                    <p>Date: {date}</p>
                    <p>Portfolio Risk Level: <span class="risk-badge">{portfolio_risk.upper()}</span></p>
                </div>

                <h2>Portfolio Overview</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Weight</th>
                            <th>Sentiment</th>
                            <th>Summary</th>
                            <th>Risk</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for ticker, weight in portfolio.items():
            data = ticker_data.get(ticker, {})
            sentiment = data.get("sentiment", 0.0)
            summary = data.get("summary", "No summary available")
            risk_level = data.get("risk_level", "medium")

            # Convert sentiment to readable label
            sentiment_label = sentiment_score_to_label(sentiment)
            
            # Sentiment class for coloring
            if sentiment > 0.05:
                sentiment_class = "sentiment-positive"
            elif sentiment < -0.05:
                sentiment_class = "sentiment-negative"
            else:
                sentiment_class = "sentiment-neutral"
            
            # Risk class for coloring
            risk_class = f"risk-{risk_level.lower()}"

            html += f"""
                        <tr>
                            <td><strong>{ticker}</strong></td>
                            <td>{weight:.1%}</td>
                            <td class="{sentiment_class}">{sentiment_label}</td>
                            <td>{summary}</td>
                            <td class="{risk_class}"><strong>{risk_level.upper()}</strong></td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>

                <h2>Source Articles</h2>
        """

        # Add article links
        for ticker, data in ticker_data.items():
            articles = data.get("articles", [])
            if articles:
                html += f"<h3>{ticker}</h3><ul>"
                for article in articles[:3]:  # Limit to 3 articles per ticker
                    html += f'<li><a href="{article.get("url", "#")}" class="article-link">{article.get("headline", "Article")}</a></li>'
                html += "</ul>"

        html += f"""
                <div class="footer">
                    <p>This is an automated report generated by Portfolio Sentiment Intelligence Agent.</p>
                    <p>For questions or concerns, please contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _generate_plain_text_email(self, report_data: dict[str, Any]) -> str:
        """Generate plain text email content."""
        portfolio = report_data.get("portfolio", {})
        ticker_data = report_data.get("ticker_data", {})
        portfolio_risk = report_data.get("portfolio_risk", "medium")
        date = report_data.get("date", "Today")

        text = f"""
Portfolio Sentiment Report
Date: {date}
Portfolio Risk Level: {portfolio_risk.upper()}

Portfolio Overview:
"""

        for ticker, weight in portfolio.items():
            data = ticker_data.get(ticker, {})
            sentiment = data.get("sentiment", 0.0)
            summary = data.get("summary", "No summary available")
            risk_level = data.get("risk_level", "medium")
            
            # Convert sentiment to readable label
            sentiment_label = sentiment_score_to_label(sentiment)

            text += f"""
{ticker}:
  Weight: {weight:.1%}
  Sentiment: {sentiment_label}
  Risk: {risk_level.upper()}
  Summary: {summary}
"""

        text += "\nSource Articles:\n"
        for ticker, data in ticker_data.items():
            articles = data.get("articles", [])
            if articles:
                text += f"\n{ticker}:\n"
                for article in articles[:3]:
                    text += f"  - {article.get('headline', 'Article')}: {article.get('url', '')}\n"

        text += "\n---\nThis is an automated report generated by Portfolio Sentiment Intelligence Agent."

        return text

