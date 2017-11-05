class UserMailer < ApplicationMailer
  helper ApplicationHelper

  def analyzer_result_notification dir_path, sources, email
    @sources = sources

    @sources.each do |source, contracts|
      attachments[source.to_s] = File.read("#{dir_path}/#{source}")
    end

    mail to: email, subject: "Analysis results by Oyente"
  end

  def bytecode_analysis_result filepath, contract, email
    @contract = contract
    attachments["Runtime bytecode"] = File.read(filepath)
    mail to: email, subject: "Bytecode analysis result by Oyente"
  end
end
