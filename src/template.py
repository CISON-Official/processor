#!/usr/bin/env python3


class EmailTemplate:

    def __init__(self):
        pass

    @staticmethod
    def preconference_template(member_name: str):
        return f"""
    <html>
<body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; padding: 20px;">
    <div style="max-width: 600px; margin: auto; background: #ffffff; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="text-align: center; padding: 20px; background-color: #f8fcf9;">
            <img src="https://my.cison.org.ng/members/wp-content/uploads/2024/09/CISON-Icon.jpg" alt="CISON Logo" style="max-width: 120px; height: auto;">
        </div>
        
        <div style="padding: 30px;">
            <h2 style="color: #1A693D; margin-top: 0;">Thank You for Attending!</h2>
            <p>Dear <strong>{member_name}</strong>,</p>
            <p>On behalf of the <strong>Chartered Institute of Statisticians of Nigeria (CISON)</strong>, we sincerely appreciate your participation in the 2025 Pre-Conference.</p>
            
            
            <div style="background-color: #f0f7f2; padding: 15px; border-left: 5px solid #1A693D; margin: 20px 0;">
                <p style="margin: 0;">We have attached your Certificate of Attendance to this email for your records.</p>
            </div>

            <p>We look forward to seeing you at future events.</p>
            <br>
            <p style="margin-bottom: 0;">Warm regards,</p>
            <strong>CISON </strong>
        </div>
        <div style="background-color: #1A693D; color: #ffffff; text-align: center; padding: 10px; font-size: 12px;">
            Chartered Institute of Statisticians of Nigeria (<b>CISON</b>)
        </div>
    </div>
</body>
</html>
    """

    @staticmethod
    def conference_template(member_name: str):
        return f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #222; line-height: 1.6; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: #ffffff; border-top: 8px solid #1A693D; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="text-align: center; padding: 25px 20px 10px 20px;">
                <img src="https://my.cison.org.ng/members/wp-content/uploads/2024/09/CISON-Icon.jpg" alt="CISON Logo" style="max-width: 130px; height: auto;">
                <h3 style="color: #1A693D; margin-top: 10px; font-size: 16px; letter-spacing: 1px;">Chartered Institute of Statisticians of Nigeria</h3>
            </div>

            <div style="padding: 20px 40px 40px 40px;">
                <h2 style="color: #1A693D; text-align: center;">Congratulations, {member_name}!</h2>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p>Thank you for being part of the <strong>2025 CISON Annual Conference</strong>.</p>
                
                <p>It was a pleasure having you join fellow Statisticians and professionals in Nigeria for last year's technical sessions and workshops.</p>
                
                <div style="background-color: #f0f7f2; padding: 25px; border-radius: 8px; text-align: center; margin: 25px 0; border: 1px solid #d1e7dd;">
                    <p style="margin-bottom: 10px; color: #1A693D; font-size: 1.1em;"><strong>Your Certificate of Participation is attached.</strong></p>
                    <p style="font-size: 0.9em; color: #555;">Please retain this document for your professional records and Continuous Professional Development</p>
                </div>
                
                <p style="margin-top: 30px;">Best Regards,<br>
                Chartered Institute of Statisticians of Nigeria <b>(CISON)</b></p>
            </div>
        </div>
    </body>
    </html>
    """

    @staticmethod
    def first_prs_template():
        return """
        <html>

        <body
            style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #222; line-height: 1.6; background-color: #f4f4f4; padding: 20px;">
            <div
                style="max-width: 600px; margin: auto; background: #ffffff; border-top: 8px solid #1A693D; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="text-align: center; padding: 25px 20px 10px 20px;">
                    <img src="https://my.cison.org.ng/members/wp-content/uploads/2024/09/CISON-Icon.jpg" alt="CISON Logo"
                        style="max-width: 130px; height: auto;">
                    <h3 style="color: #1A693D; margin-top: 10px; font-size: 16px; letter-spacing: 1px;">Chartered Institute of
                        Statisticians of Nigeria</h3>
                </div>

                <div style="padding: 20px 40px 40px 40px;">
                    <h2 style="color: #1A693D; text-align: center;">Dear member,</h2>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">

                    <p>Thank you for joining us for CISON’s first PRS on <strong>Advances in Statistics: AI and Computational
                            Tools</strong>x.</p>

                    <p>It was a pleasure to have you in the session. We hope you found the insights both practical and
                        thought-provoking for your professional toolkit.</p>

                    <div
                        style="background-color: #f0f7f2; padding: 25px; border-radius: 8px; text-align: center; margin: 25px 0; border: 1px solid #d1e7dd;">
                        <p style="margin-bottom: 10px; color: #1A693D; font-size: 1.1em;"><strong>Your Certificate of
                                attendance is attached.</strong></p>
                        <p style="font-size: 0.9em; color: #555;">Please retain this document for your professional records and
                            Continuous Professional Development</p>
                    </div>

                    <p style="margin-top: 30px;">Best Regards,<br>
                        Chartered Institute of Statisticians of Nigeria <b>(CISON)</b></p>
                </div>
            </div>
        </body>

        </html>
        """
