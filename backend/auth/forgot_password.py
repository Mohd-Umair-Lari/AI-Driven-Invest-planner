import os
import resend
from typing import Tuple

class ForgotPasswordService:
    """Service for handling forgot password email notifications"""
    
    def __init__(self):
        api_key = os.getenv("RESEND_API_KEY")
        if api_key:
            resend.api_key = api_key
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@finpassai.com")
        self.app_url = os.getenv("APP_URL", "https://ai-driven-invest-planner.vercel.app")
    
    def send_reset_email(self, email: str, reset_token: str) -> Tuple[bool, str]:
        try:
            reset_link = f"{self.app_url}/static/reset_password.html?token={reset_token}"
            
            html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: 'Inter', system-ui, sans-serif; background: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .logo {{ font-size: 24px; font-weight: bold; color: #000; margin-bottom: 10px; }}
                        .header p {{ color: #666; margin: 0; }}
                        .content {{ color: #333; line-height: 1.6; }}
                        .reset-button {{ display: inline-block; background: linear-gradient(135deg, #EF4444, #DC2626); color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; margin: 20px 0; font-weight: 600; }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center; }}
                        .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 6px; margin: 20px 0; color: #856404; font-size: 14px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">💰 FinPass AI</div>
                            <p>Password Reset Request</p>
                        </div>
                        
                        <div class="content">
                            <p>Hi,</p>
                            
                            <p>We received a request to reset your FinPass AI password. Click the button below to proceed:</p>
                            
                            <div style="text-align: center;">
                                <a href="{reset_link}" class="reset-button">Reset Password</a>
                            </div>
                            
                            <p>Or copy and paste this link in your browser:</p>
                            <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 6px; font-size: 12px;">
                                {reset_link}
                            </p>
                            
                            <div class="warning">
                                <strong>⚠️ Important:</strong> This link will expire in 24 hours. If you didn't request a password reset, please ignore this email.
                            </div>
                            
                            <p>For security reasons, never share this link with anyone.</p>
                            
                            <p>Best regards,<br>The FinPass AI Team</p>
                        </div>
                        
                        <div class="footer">
                            <p>© 2026 FinPass AI. All rights reserved.</p>
                            <p>This is an automated email. Please do not reply directly.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            response = resend.Emails.send({
                "from": self.sender_email,
                "to": email,
                "subject": "Reset Your FinPass AI Password",
                "html": html_content,
            })
            
            if response.get("id"):
                return True, "Password reset email sent successfully"
            else:
                return False, f"Failed to send email: {response.get('message', 'Unknown error')}"
        
        except Exception as e:
            return False, f"Error sending reset email: {str(e)}"
    
    def send_password_changed_email(self, email: str) -> Tuple[bool, str]:
        try:
            html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: 'Inter', system-ui, sans-serif; background: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .logo {{ font-size: 24px; font-weight: bold; color: #000; margin-bottom: 10px; }}
                        .success-icon {{ font-size: 48px; margin: 20px 0; }}
                        .content {{ color: #333; line-height: 1.6; }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">💰 FinPass AI</div>
                            <p>Password Changed Successfully</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <div class="success-icon">✅</div>
                        </div>
                        
                        <div class="content">
                            <p>Hi,</p>
                            
                            <p>Your password has been successfully changed. You can now log in to your FinPass AI account with your new password.</p>
                            
                            <p>If you did not make this change or suspect unauthorized access, please contact our support team immediately.</p>
                            
                            <p>Best regards,<br>The FinPass AI Team</p>
                        </div>
                        
                        <div class="footer">
                            <p>© 2026 FinPass AI. All rights reserved.</p>
                            <p>This is an automated email. Please do not reply directly.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            response = resend.Emails.send({
                "from": self.sender_email,
                "to": email,
                "subject": "Your FinPass AI Password Has Been Changed",
                "html": html_content,
            })
            
            if response.get("id"):
                return True, "Confirmation email sent successfully"
            else:
                return False, f"Failed to send email: {response.get('message', 'Unknown error')}"
        
        except Exception as e:
            return False, f"Error sending confirmation email: {str(e)}"


forgot_password_service = ForgotPasswordService()