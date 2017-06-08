class HomeController < ApplicationController
  def index
  end

  def analyze
    upload_path = Rails.root.join('public', 'uploads')
    filepath = upload_path.join('tmp.sol')

    Dir.mkdir(upload_path) unless Dir.exists?(upload_path)

    File.open(filepath, 'wb') do |file|
      file.write(oyente_params[:source])
    end

    @output = `python #{ENV['OYENTE']}/oyente.py -s #{filepath} -w#{options} `

    UserMailer.analyzer_result_notification(oyente_params[:filename], filepath.to_s, @output, oyente_params[:email]).deliver_later
  end

  private
  def oyente_params
    params.require(:data).permit(:filename, :source, :timeout, :global_timeout, :depthlimit, :gaslimit, :looplimit, :email)
  end

  def options
    opts = ""
    oyente_params.each do |opt, val|
      unless ["source", "filename", "email"].include?(opt)
        val = seconds_to_milliseconds(val) if opt == "timeout"
        opt = opt.gsub(/_/, '-')
        opts += " --#{opt} #{val}"
      end
    end
    return opts
  end

  def seconds_to_milliseconds second
    ( second.to_f * 1000 ).to_i
  end
end
