module ByteCodeHelper
  def bug_exists_for_bytecode? bool
    if bool
      return "<span style='color: red'>True</span>".html_safe
    else
      return "<span style='color: green'>False</span>".html_safe
    end
  end

  def any_vulnerability_for_bytecode? contract
    contract[:vulnerabilities].each do |vul, bool|
      return true if bool
    end
    return false
  end

  def border_color_for_bytecode contract
    if any_vulnerability_for_bytecode?(contract)
      "warning-box"
    else
      "safe-box"
    end
  end
end
