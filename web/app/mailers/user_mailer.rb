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

  def bytecode_analysis_result filepath, result, email
    @result = result
    attachments["result"] = File.read(filepath)
    mail to: email, subject: "Bytecode analysis result by Oyente"
  end
end
