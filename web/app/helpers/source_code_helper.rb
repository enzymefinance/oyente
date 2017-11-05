module SourceCodeHelper
  def any_vulnerability? contract
    contract[:vulnerabilities].each do |vul, warnings|
      return true unless warnings.empty?
    end
    return false
  end

  def vulnerability_names
    return {
      callstack: "Callstack Depth Attack Vulnerability",
      time_dependency: "Timestamp Dependency",
      reentrancy: "Re-Entrancy Vulnerability",
      money_concurrency: "Transaction-Ordering Dependence (TOD)",
      assertion_failure: "Assertion Failure"
    }
  end

  def border_color contract
    if any_vulnerability?(contract)
      "warning-box"
    else
      "safe-box"
    end
  end
end
