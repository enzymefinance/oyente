class HomeController < ApplicationController
  def index
  end

  def analyze
    @sources = {}

    if bytecode_exists?
      @sources[:error] = "Error"
      return
    end

    @sources[:current_file] = oyente_params[:current_file]
    unless check_params
      @sources[:error] = "Invalid input"
    else
      FileUtils::mkdir_p "tmp/contracts"
      current_filename = oyente_params[:current_file].split("/")[-1]
      dir_path = Dir::Tmpname.make_tmpname "tmp/contracts/#{current_filename}", nil
      sources = eval(oyente_params[:sources])
      structure_files sources, dir_path
      file = File.open("#{dir_path}/#{oyente_params[:current_file]}", "r")
      begin
        output = oyente_cmd(file.path, "#{options} -a -rp #{dir_path}")
        @sources = eval(output)
        UserMailer.analyzer_result_notification(dir_path, @sources, oyente_params[:email]).deliver_later unless oyente_params[:email].nil?
      rescue
        @sources[:error] = "Error"
      ensure
        file.close
      end
    end
  end

  def analyze_bytecode
    @contract = {}
    unless bytecode_exists?
      @contract[:error] = "Error"
      return
    end

    unless check_params
      @contract[:error] = "Invalid input"
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
      @contract[:error] = "Error"
      return
    ensure
      file.close
    end

    begin
      output = oyente_cmd(file.path, "#{options} -b")
      @contract = eval(output)
      UserMailer.bytecode_analysis_result(file.path, @contract, oyente_params[:email]).deliver_later unless oyente_params[:email].nil?
    rescue
      @contract[:error] = "Error"
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
