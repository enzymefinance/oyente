# Preview all emails at http://localhost:3000/rails/mailers/user_mailer
class UserMailerPreview < ActionMailer::Preview

  # Preview this email at http://localhost:3000/rails/mailers/user_mailer/analyzer_result_notification
  def analyzer_result_notification
    UserMailer.analyzer_result_notification
  end

end
