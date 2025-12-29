"""Email Agent - formats and delivers email reports."""

from datetime import datetime
from typing import Any, Dict

from db import db_manager, User, EmailLog
from agents.base_agent import BaseAgent
from agents.schemas import EmailInput, EmailOutput
from services.email_service import EmailService


class EmailAgent(BaseAgent):
    """Agent for sending email reports."""

    def __init__(self):
        """Initialize Email Agent."""
        super().__init__("EmailAgent")
        self.email_service = EmailService()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email report.

        Args:
            input_data: Must contain:
                - 'user_email': email address
                - 'portfolio': dict of {ticker: weight}
                - 'ticker_data': dict of {ticker: {sentiment, summary, risk_level, articles}}
                - 'portfolio_risk': overall risk level
                - 'date': report date

        Returns:
            Dictionary with 'success' and optional 'error_message'.
        """
        # Validate input
        email_input = EmailInput(**input_data)

        self.logger.info(f"Sending email report to {email_input.user_email}")

        # Prepare report data
        report_data = {
            "portfolio": email_input.portfolio,
            "ticker_data": email_input.ticker_data,
            "portfolio_risk": email_input.portfolio_risk,
            "date": email_input.date or datetime.now().strftime("%Y-%m-%d"),
        }

        # Send email
        success = self.email_service.send_report(email_input.user_email, report_data)

        # Log delivery status
        user_id = input_data.get("user_id")
        if user_id:
            self._log_email_delivery(user_id, success, None if success else "Email delivery failed")

        if success:
            self.logger.info(f"Email sent successfully to {email_input.user_email}")
        else:
            self.logger.error(f"Failed to send email to {email_input.user_email}")

        # Return output
        output = EmailOutput(success=success, error_message=None if success else "Email delivery failed")
        return output.model_dump()

    def _log_email_delivery(self, user_id: int, success: bool, error_message: str | None) -> None:
        """Log email delivery status.

        Args:
            user_id: User ID.
            success: Whether email was sent successfully.
            error_message: Error message if failed.
        """
        try:
            with db_manager.get_session() as session:
                email_log = EmailLog(
                    user_id=user_id,
                    status="sent" if success else "failed",
                    error_message=error_message,
                )
                session.add(email_log)
                session.commit()
        except Exception as e:
            self.logger.warning(f"Error logging email delivery: {e}")

