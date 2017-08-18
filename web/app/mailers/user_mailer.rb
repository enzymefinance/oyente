class UserMailer < ApplicationMailer
  helper ApplicationHelper

  def analyzer_result_notification filepath, results, email
    @results = results

    attachments[@results[:filename]] = File.read(filepath)

    mail to: email, subject: "Analysis results by Oyente"
  end
end
