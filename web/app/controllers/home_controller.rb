class HomeController < ApplicationController
  def index
  end

  def analyze
    @results = {}

    if bytecode_exists?
      @results[:error] = "Error"
      return
    end

    @results[:current_file] = oyente_params[:current_file]
    unless check_params
      @results[:error] = "Invalid input"
    else
      FileUtils::mkdir_p "tmp/contracts"
      current_filename = oyente_params[:current_file].split("/")[-1]
      dir_path = Dir::Tmpname.make_tmpname "tmp/contracts/#{current_filename}", nil
      sources = eval(oyente_params[:sources])
      structure_files sources, dir_path
      file = File.open("#{dir_path}/#{oyente_params[:current_file]}", "r")
      begin
        output = oyente_cmd(file.path, "#{options} -a -rp #{dir_path}")
        @results = eval(output)
        UserMailer.analyzer_result_notification(dir_path, @results, oyente_params[:email]).deliver_later unless oyente_params[:email].nil?
      rescue
        @results[:error] = "Error"
      ensure
        file.close
      end
    end
  end

  def analyze_bytecode
    @result = {}
    unless bytecode_exists?
      @result[:error] = "Error"
      render :analyze and return
    end

    unless check_params
      @result[:error] = "Invalid input"
      return
    end

    FileUtils::mkdir_p "tmp/contracts"
    dir_path = "tmp/contracts/bytecode_#{request.remote_ip}"
    FileUtils::mkdir_p dir_path
    filepath = Dir::Tmpname.make_tmpname("#{dir_path}/result_", nil)

    file = File.open("#{filepath}", "w")
    begin
      file.write(oyente_params[:bytecode].gsub(/^0x/, ""))
    rescue
      @result[:error] = "Error"
      return
    ensure
      file.close
    end

    begin
      output = oyente_cmd(file.path, "#{options} -b")
      error = output.split("======= error =======\n", 2)
      if error.size > 1
        @result[:error] = error[1]
      else
        result = output.split("======= results =======\n")[1]
        result = eval(result)
        @result[:result] = result
      end
      UserMailer.bytecode_analysis_result(file.path, @result, oyente_params[:email]).deliver_later unless oyente_params[:email].nil?
    rescue
      @result[:error] = "Error"
    end
  end

  private
  def structure_files sources, dir_path
    sources.each do |key, value|
      if value.key?(:"/content")
        file = key
        File.open "#{dir_path}/#{file}", "w" do |f|
          f.write value[:"/content"]
        end
      else
        dir = key
        new_dir_path = "#{dir_path}/#{dir}"
        FileUtils::mkdir_p new_dir_path
        structure_files value, new_dir_path
      end
    end
  end

  def oyente_cmd filepath, options
    return `python #{ENV['OYENTE']}/oyente.py -s #{filepath} -w#{options}`
  end

  def bytecode_exists?
    return !oyente_params[:bytecode].nil?
  end

  def oyente_params
    params.require(:data).permit(:current_file, :sources, :timeout, :global_timeout, :depthlimit, :gaslimit, :looplimit, :email, :bytecode)
  end

  def check_params
    oyente_params.each do |opt, val|
      unless ["sources", "current_file", "email", "bytecode"].include?(opt)
        return false unless is_number?(val)
      end
    end
    return true
  end

  def options
    opts = ""
    oyente_params.each do |opt, val|
      unless ["sources", "current_file", "email", "bytecode"].include?(opt)
        opt = opt.gsub(/_/, '-')
        opts += " --#{opt} #{val}"
      end
    end
    return opts
  end

  def is_number? string
    true if Integer(string) && Integer(string) > 0 rescue false
  end
end
