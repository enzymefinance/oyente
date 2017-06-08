class UserMailer < ApplicationMailer

  # Subject can be set in your I18n file at config/locales/en.yml
  # with the following lookup:
  #
  #   en.user_mailer.analyzer_result_notification.subject
  #
  def analyzer_result_notification filename, filepath, result, email
    @filename = filename
    @result = result

    attachments[filename] = File.read(filepath)

    FileUtils.rm_r Dir.glob('public/uploads/*')

    mail to: email, subject: "The analysis of a smart contract from Oyente"
  end
end
