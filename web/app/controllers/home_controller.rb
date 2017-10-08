class HomeController < ApplicationController
  def index
  end

  def analyze
    @results = {}
    @results[:current_file] = oyente_params[:current_file]
    unless check_params
      @results[:error] = "Invalid input"
    else
      FileUtils::mkdir_p "tmp/contracts"
      dir_path = Dir::Tmpname.make_tmpname "tmp/contracts/#{oyente_params[:current_file]}", nil
      FileUtils::mkdir_p dir_path
      sources = eval(oyente_params[:sources])
      sources.keys.each do |filename|
        File.open "#{dir_path}/#{filename}", "w" do |f|
          f.write sources[filename][:"/content"]
        end
      end
      file = File.open("#{dir_path}/#{oyente_params[:current_file]}", "r")
      begin
        output = `python #{ENV['OYENTE']}/oyente.py -s #{file.path} -w#{options} -a`
        error = output.split("======= error =======\n", 2)
        if error.size > 1
          @results[:error] = error[1]
        else
          @results[:contracts] = {}
          output = output.split("======= results =======\n")
          output[1..-1].each do |results|
            results = eval(results)
            filename = results[:filename]
            if @results[:contracts].key?(filename)
              @results[:contracts][filename] << results
            else
              @results[:contracts][filename] = [results]
            end
          end
        end
        UserMailer.analyzer_result_notification(dir_path, @results, oyente_params[:email]).deliver_later unless oyente_params[:email].nil?
      rescue
        @results[:error] = "Error"
      ensure
        file.close
      end
    end
  end

  private
  def oyente_params
    params.require(:data).permit(:current_file, :sources, :timeout, :global_timeout, :depthlimit, :gaslimit, :looplimit, :email)
  end

  def check_params
    oyente_params.each do |opt, val|
      unless ["sources", "current_file", "email"].include?(opt)
        return false unless is_number?(val)
      end
    end
    return true
  end

  def options
    opts = ""
    oyente_params.each do |opt, val|
      unless ["sources", "current_file", "email"].include?(opt)
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
