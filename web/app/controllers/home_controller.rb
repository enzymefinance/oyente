class HomeController < ApplicationController
  before_action :check_file, only: :upload

  def index
  end

  def upload
    filepath = Rails.root.join('public', 'uploads', 'tmp.sol')

    File.open(filepath, 'wb') do |file|
      file.write(upload_io)
    end

    @output = `python #{ENV['OYENTE']}/oyente.py -s #{filepath}`
    FileUtils.rm_r Dir.glob('public/uploads/*')
  end

  private
  def upload_io
    params[:coding_file]
  end

  def check_file
    redirect_to root_url if upload_io.nil? || upload_io.class.name != "String"
  end
end
