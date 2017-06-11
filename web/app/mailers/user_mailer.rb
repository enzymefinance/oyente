class UserMailer < ApplicationMailer
  def analyzer_result_notification filename, filepath, result, email
    @filename = filename
    @result = result

    attachments[filename] = File.read(filepath)

    File.delete(filepath)

    mail to: email, subject: "Analysis results by Oyente"
  end
end
