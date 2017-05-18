class HomeController < ApplicationController
  before_action :check_file, only: :upload

  def index
  end

  def upload
    filepath = Rails.root.join('public', 'uploads', upload_io.original_filename)

    File.open(filepath, 'wb') do |file|
      file.write(upload_io.read)
    end

    @output = `python #{ENV['OYENTE']}/oyente.py -s #{filepath}`
    FileUtils.rm_r Dir.glob('public/uploads/*')
  end

  private
  def upload_io
    params[:coding_file]
  end

  def check_file
    if upload_io.nil?
      redirect_to root_url
    else
      extname = File.extname(upload_io.original_filename)
      redirect_to root_url unless extname == ".sol"
    end
  end
end
