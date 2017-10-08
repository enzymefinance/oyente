class UserMailer < ApplicationMailer
  helper ApplicationHelper

  def analyzer_result_notification dir_path, results, email
    @results = results

    @results[:contracts].each do |filename, result|
      filepath = "#{dir_path}/#{filename}"
      attachments[filename] = File.read(filepath)
    end

    mail to: email, subject: "Analysis results by Oyente"
  end
end
