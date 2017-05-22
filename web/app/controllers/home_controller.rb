class HomeController < ApplicationController
  def index
  end

  def analyze
    filepath = Rails.root.join('public', 'uploads', 'tmp.sol')

    File.open(filepath, 'wb') do |file|
      file.write(oyente_params[:source])
    end

    @output = `python #{ENV['OYENTE']}/oyente.py -s #{filepath} #{options} `
    FileUtils.rm_r Dir.glob('public/uploads/*')
  end

  private
  def oyente_params
    params.require(:data).permit(:source, :timeout, :depthlimit, :gaslimit, :looplimit)
  end

  def options
    opts = ""
    oyente_params.each do |opt, val|
      unless opt == "source"
        opts += "--#{opt} #{val}"
      end
    end
    return opts
  end
end
