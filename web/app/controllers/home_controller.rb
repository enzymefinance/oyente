class HomeController < ApplicationController
  def index
  end

  def analyze
    @results = {}
    @results[:filename] = oyente_params[:filename]
    unless check_params
      @results[:error] = "Invalid input"
    else
      file = Tempfile.new oyente_params[:filename]
      begin
        file.write oyente_params[:source]
        file.close
        output = `python #{ENV['OYENTE']}/oyente.py -s #{file.path} -w#{options} -a --no-debug`
        error = output.split("======= error =======\n", 2)
        if error.size > 1
          @results[:error] = error[1]
        else
          @results[:contracts] = []
          output = output.split("======= results =======\n")
          output[1..-1].each do |result|
            @results[:contracts] << eval(result)
          end
        end
        UserMailer.analyzer_result_notification(file.path, @results, oyente_params[:email]).deliver_later
      rescue
        file.close
        @results[:error] = "Error"
      end
    end
  end

  private
  def oyente_params
    params.require(:data).permit(:filename, :source, :timeout, :global_timeout, :depthlimit, :gaslimit, :looplimit, :email)
  end

  def check_params
    oyente_params.each do |opt, val|
      unless ["source", "filename", "email"].include?(opt)
        return false unless is_number?(val)
      end
    end
    return true
  end

  def options
    opts = ""
    oyente_params.each do |opt, val|
      unless ["source", "filename", "email"].include?(opt)
        opt = opt.gsub(/_/, '-')
        opts += " --#{opt} #{val}"
      end
    end
    return opts
  end

  def is_number? string
    true if Float(string) rescue false
  end
end
