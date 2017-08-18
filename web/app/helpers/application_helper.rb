module ApplicationHelper
  def bug_exists? msg
    if msg.empty?
      return "<span style='color: green'>False</span>".html_safe
    else
      return "<span style='color: red'>True</span>".html_safe
    end
  end
end
