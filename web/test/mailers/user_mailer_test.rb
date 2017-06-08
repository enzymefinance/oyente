require 'test_helper'

class UserMailerTest < ActionMailer::TestCase
  test "analyzer_result_notification" do
    mail = UserMailer.analyzer_result_notification
    assert_equal "Analyzer result notification", mail.subject
    assert_equal ["to@example.org"], mail.to
    assert_equal ["from@example.com"], mail.from
    assert_match "Hi", mail.body.encoded
  end

end
