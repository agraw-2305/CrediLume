// CrediLume EMI Calculator - Clean Implementation
(function() {
  'use strict';
  
  console.log('CrediLume Calculator v2 loaded');

  // Currency configuration
  let currentCurrency = 'USD';
  let currentLocale = 'en-US';
  let currentSymbol = '$';
  
  // Currency-specific amount presets
  const currencyPresets = {
    USD: [10000, 25000, 50000, 100000, 250000],
    EUR: [10000, 25000, 50000, 100000, 250000],
    GBP: [10000, 25000, 50000, 100000, 250000],
    INR: [100000, 500000, 1000000, 2500000, 5000000],
    JPY: [1000000, 2500000, 5000000, 10000000, 25000000],
    CNY: [50000, 100000, 250000, 500000, 1000000],
    CAD: [10000, 25000, 50000, 100000, 250000],
    AUD: [10000, 25000, 50000, 100000, 250000],
    CHF: [10000, 25000, 50000, 100000, 250000],
    SGD: [10000, 25000, 50000, 100000, 250000],
    AED: [50000, 100000, 250000, 500000, 1000000],
    BRL: [50000, 100000, 250000, 500000, 1000000],
    MXN: [100000, 250000, 500000, 1000000, 2500000],
    KRW: [10000000, 25000000, 50000000, 100000000, 250000000],
    ZAR: [100000, 250000, 500000, 1000000, 2500000]
  };

  // Dynamic formatters
  let fmt = new Intl.NumberFormat(currentLocale, { maximumFractionDigits: 0 });
  let currency = new Intl.NumberFormat(currentLocale, { style: 'currency', currency: currentCurrency, maximumFractionDigits: 0 });

  // Calculation limits (tune these if you want)
  // NOTE: JS numbers cannot precisely represent integers > Number.MAX_SAFE_INTEGER
  const MAX_PRINCIPAL_DEFAULT = Number.MAX_SAFE_INTEGER;
  const MAX_PRINCIPAL_BY_CURRENCY = {
    // Example overrides (optional):
    // INR: 1000000000000000, // 1,000,000 Cr
  };

  function updateFormatters() {
    fmt = new Intl.NumberFormat(currentLocale, { maximumFractionDigits: 0 });
    currency = new Intl.NumberFormat(currentLocale, { style: 'currency', currency: currentCurrency, maximumFractionDigits: 0 });
  }

  function getMaxPrincipal() {
    const byCurrency = MAX_PRINCIPAL_BY_CURRENCY[currentCurrency];
    const max = typeof byCurrency === 'number' ? byCurrency : MAX_PRINCIPAL_DEFAULT;
    return Math.min(max, Number.MAX_SAFE_INTEGER);
  }

  function symbolPrefix() {
    const sym = String(currentSymbol || '').trim();
    if (!sym) return '';
    // Add a space for alphabetic symbols like "Rp", "RM", "Fr", "kr".
    const alphaLike = /^[A-Za-z]{1,4}$/.test(sym) || (/[A-Za-z]/.test(sym) && !/[$€£¥₹₩฿₱]/.test(sym));
    return alphaLike ? (sym + ' ') : sym;
  }

  function formatCompactValue(value) {
    const abs = Math.abs(value);
    const prefix = symbolPrefix();

    if (currentCurrency === 'JPY' || currentCurrency === 'KRW') {
      if (abs >= 100000000) return prefix + (value / 100000000).toFixed(abs >= 1000000000 ? 0 : 1) + '億';
      if (abs >= 10000) return prefix + (value / 10000).toFixed(abs >= 100000 ? 0 : 1) + '万';
      return currency.format(value);
    }

    if (currentCurrency === 'INR') {
      if (abs >= 10000000) return '₹' + (value / 10000000).toFixed(abs >= 100000000 ? 0 : 1) + 'Cr';
      if (abs >= 100000) return '₹' + (value / 100000).toFixed(abs >= 1000000 ? 0 : 1) + 'L';
      return currency.format(value);
    }

    if (abs >= 1e12) return prefix + (value / 1e12).toFixed(abs >= 1e13 ? 0 : 1) + 'T';
    if (abs >= 1e9) return prefix + (value / 1e9).toFixed(abs >= 1e10 ? 0 : 1) + 'B';
    if (abs >= 1e6) return prefix + (value / 1e6).toFixed(abs >= 1e7 ? 0 : 1) + 'M';
    if (abs >= 1e3) return prefix + (value / 1e3).toFixed(abs >= 1e4 ? 0 : 1) + 'K';
    return currency.format(value);
  }

  function formatCurrencyAdaptive(value, maxLen = 18) {
    if (!Number.isFinite(value)) return '—';
    const full = currency.format(value);
    if (full.length <= maxLen) return full;
    return formatCompactValue(value);
  }

  function fitEmiText(displayText) {
    if (!monthlyPaymentEl) return;
    const len = String(displayText || '').length;
    // Soft scaling: keep it big for normal values, shrink for long strings.
    let rem = 3.0;
    if (len > 18) rem = 2.6;
    if (len > 24) rem = 2.2;
    if (len > 30) rem = 1.9;
    if (len > 36) rem = 1.6;
    monthlyPaymentEl.style.fontSize = rem + 'rem';
    monthlyPaymentEl.style.lineHeight = '1.05';
  }

  function formatCompact(value) {
    if (currentCurrency === 'JPY' || currentCurrency === 'KRW') {
      if (value >= 100000000) return currentSymbol + (value / 100000000).toFixed(0) + '億';
      if (value >= 10000) return currentSymbol + (value / 10000).toFixed(0) + '万';
      return currentSymbol + fmt.format(value);
    }
    if (currentCurrency === 'INR') {
      if (value >= 10000000) return '₹' + (value / 10000000).toFixed(1) + 'Cr';
      if (value >= 100000) return '₹' + (value / 100000).toFixed(0) + 'L';
      return '₹' + fmt.format(value);
    }
    if (value >= 1000000000000) return symbolPrefix() + (value / 1000000000000).toFixed(1) + 'T';
    if (value >= 1000000000) return symbolPrefix() + (value / 1000000000).toFixed(1) + 'B';
    if (value >= 1000000) return symbolPrefix() + (value / 1000000).toFixed(1) + 'M';
    if (value >= 1000) return symbolPrefix() + (value / 1000).toFixed(0) + 'K';
    return currentSymbol + fmt.format(value);
  }

  // DOM Elements
  const $ = (id) => document.getElementById(id);
  
  const loanAmountEl = $('loan_amount');
  const tenureMonthsEl = $('tenure_months');
  const tenureLabelEl = $('tenureLabel');
  const tenureTypedEl = $('tenure_typed');
  const tenureUnitSelectEl = $('tenure_unit_select');
  const interestRateEl = $('interest_rate');
  const interestRateLabelEl = $('interest_rate_label');
  
  const monthlyPaymentEl = $('monthly_payment');
  const principalTotalEl = $('principal_total');
  const interestTotalEl = $('interest_total');
  const totalCostEl = $('total_cost');
  const interestPctEl = $('interest_pct');
  const interestSummaryLineEl = $('interestSummaryLine');
  const chartHintEl = $('chartHint');
  
  const affordabilityTextEl = $('affordabilityText');
  const affordMeterFillEl = $('affordMeterFill');
  const affordMeterLabelEl = $('affordMeterLabel');
  
  const aiSavingsLineEl = $('aiSavingsLine');
  const aiAffordLineEl = $('aiAffordLine');
  const aiNextStepsEl = $('aiNextSteps');
  
  const stressRateEl = $('stress_rate');
  const stressLabelEl = $('stressLabel');
  const stressResultEl = $('stressResult');
  
  const amortKeyBodyEl = $('amortKeyBody');
  const amortKeyHintEl = $('amortKeyHint');
  
  const incomeEl = $('income_annum');
  const loanTypeEl = $('loan_type');
  
  const setupPctEl = $('setupPct');

  let chart = null;

  // EMI Calculation
  function calculateEMI(principal, months, annualRate) {
    if (principal <= 0 || months <= 0) return null;
    
    const monthlyRate = (annualRate / 100) / 12;
    
    let emi;
    if (monthlyRate === 0) {
      emi = principal / months;
    } else {
      const pow = Math.pow(1 + monthlyRate, months);
      emi = principal * (monthlyRate * pow) / (pow - 1);
    }
    
    const totalAmount = emi * months;
    const totalInterest = totalAmount - principal;
    
    return {
      emi: emi,
      totalInterest: totalInterest,
      totalAmount: totalAmount
    };
  }

  // Generate amortization schedule
  function generateSchedule(principal, months, annualRate) {
    if (principal <= 0 || months <= 0) return [];
    
    const monthlyRate = (annualRate / 100) / 12;
    const result = calculateEMI(principal, months, annualRate);
    if (!result) return [];
    
    const emi = result.emi;
    let balance = principal;
    const rows = [];
    
    for (let i = 1; i <= months; i++) {
      const interest = monthlyRate === 0 ? 0 : balance * monthlyRate;
      const principalPaid = emi - interest;
      balance = Math.max(0, balance - principalPaid);
      rows.push({ month: i, emi, principal: principalPaid, interest, balance });
    }
    
    return rows;
  }

  // Update tenure label
  function updateTenureLabel() {
    if (!tenureMonthsEl || !tenureLabelEl) return;
    const months = parseInt(tenureMonthsEl.value) || 120;
    const years = Math.floor(months / 12);
    const rem = months % 12;
    let label = years + (years === 1 ? ' year' : ' years');
    if (rem > 0) label += ' ' + rem + ' months';
    tenureLabelEl.textContent = label + ' / ' + months + ' months';
    
    // Sync typed tenure
    if (tenureTypedEl && tenureUnitSelectEl) {
      const unit = tenureUnitSelectEl.value;
      tenureTypedEl.value = unit === 'years' ? Math.round(months / 12) : months;
    }
  }

  // Update interest rate label
  function updateRateLabel() {
    if (!interestRateEl || !interestRateLabelEl) return;
    const rate = parseFloat(interestRateEl.value) || 10;
    interestRateLabelEl.textContent = rate.toFixed(1) + '%';
  }

  // Update chart
  function updateChart(principal, interest) {
    const ctx = $('breakdownChart');
    if (!ctx) return;
    
    const data = [principal || 0, interest || 0];
    
    if (!chart) {
      chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Principal', 'Interest'],
          datasets: [{
            data: data,
            backgroundColor: ['#1e293b', '#0ea5e9'],
            borderWidth: 0
          }]
        },
        options: {
          cutout: '70%',
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (c) => c.label + ': ' + currency.format(c.raw)
              }
            }
          }
        }
      });
    } else {
      chart.data.datasets[0].data = data;
      chart.update();
    }
  }

  // Update amortization preview - show first 24 months
  function updateAmortPreview(schedule, principal) {
    if (!amortKeyBodyEl) return;
    amortKeyBodyEl.innerHTML = '';
    
    if (!schedule || schedule.length === 0) {
      if (amortKeyHintEl) amortKeyHintEl.textContent = 'Enter valid loan details to see key moments.';
      return;
    }
    
    if (amortKeyHintEl) amortKeyHintEl.textContent = 'Showing first 24 months of your loan schedule.';
    
    // Show first 24 months (or all if less than 24)
    const monthsToShow = Math.min(24, schedule.length);
    
    for (let i = 0; i < monthsToShow; i++) {
      const row = schedule[i];
      const tr = document.createElement('tr');
      tr.className = i % 2 === 0 ? 'bg-white' : 'bg-slate-50';
      tr.innerHTML = `
        <td class="px-2 py-1.5 text-slate-600 font-medium">${row.month}</td>
        <td class="px-2 py-1.5">${formatCurrencyAdaptive(row.emi, 18)}</td>
        <td class="px-2 py-1.5 text-emerald-600">${formatCurrencyAdaptive(row.principal, 18)}</td>
        <td class="px-2 py-1.5 text-amber-600">${formatCurrencyAdaptive(row.interest, 18)}</td>
        <td class="px-2 py-1.5 font-medium">${formatCurrencyAdaptive(row.balance, 18)}</td>
      `;
      amortKeyBodyEl.appendChild(tr);
    }
  }

  // Main calculate function
  function calculate() {
    console.log('calculate() called');
    
    // Get values
    const principal = parseFloat(loanAmountEl?.value) || 0;
    const months = parseInt(tenureMonthsEl?.value) || 120;
    const rate = parseFloat(interestRateEl?.value) || 10;

    // Enforce a max principal (configurable per currency)
    const maxPrincipal = getMaxPrincipal();
    if (principal > maxPrincipal) {
      const maxStr = currency.format(maxPrincipal);
      if (monthlyPaymentEl) monthlyPaymentEl.textContent = 'Max: ' + formatCompactValue(maxPrincipal);
      fitEmiText(monthlyPaymentEl ? monthlyPaymentEl.textContent : '');
      if (principalTotalEl) principalTotalEl.textContent = '≤ ' + formatCompactValue(maxPrincipal);
      if (interestTotalEl) interestTotalEl.textContent = '—';
      if (totalCostEl) totalCostEl.textContent = '—';
      if (interestPctEl) interestPctEl.textContent = '—';
      if (interestSummaryLineEl) interestSummaryLineEl.textContent = 'Please enter a loan amount up to ' + maxStr + ' to calculate accurately.';
      if (chartHintEl) chartHintEl.textContent = 'Loan amount exceeds supported range.';
      updateChart(0, 0);
      updateAmortPreview(null, 0);
      updateAiInsight(null);
      return;
    }
    
    console.log('Values: P=' + principal + ', M=' + months + ', R=' + rate);
    
    // Update labels
    updateTenureLabel();
    updateRateLabel();
    
    // Calculate EMI
    const result = calculateEMI(principal, months, rate);
    
    if (!result || principal <= 0) {
      // Show placeholder text
      if (monthlyPaymentEl) monthlyPaymentEl.textContent = 'Enter loan details to see your EMI';
      if (principalTotalEl) principalTotalEl.textContent = 'Enter amount';
      if (interestTotalEl) interestTotalEl.textContent = 'Enter details';
      if (totalCostEl) totalCostEl.textContent = 'Enter details';
      if (interestPctEl) interestPctEl.textContent = '—';
      if (interestSummaryLineEl) interestSummaryLineEl.textContent = "You'll see totals once inputs are valid.";
      if (chartHintEl) chartHintEl.textContent = 'Enter loan details to see the principal vs interest split.';
      updateChart(0, 0);
      updateAmortPreview(null, 0);
      updateAiInsight(null);
      return;
    }
    
    console.log('EMI calculated:', result.emi);
    
    // Display EMI (and guard against overflow)
    if (!Number.isFinite(result.emi) || !Number.isFinite(result.totalAmount) || !Number.isFinite(result.totalInterest)) {
      if (monthlyPaymentEl) monthlyPaymentEl.textContent = 'Result too large';
      fitEmiText(monthlyPaymentEl ? monthlyPaymentEl.textContent : '');
      if (principalTotalEl) principalTotalEl.textContent = currency.format(principal);
      if (interestTotalEl) interestTotalEl.textContent = '—';
      if (totalCostEl) totalCostEl.textContent = '—';
      if (interestPctEl) interestPctEl.textContent = '—';
      if (interestSummaryLineEl) interestSummaryLineEl.textContent = 'Try a smaller loan amount or shorter tenure.';
      if (chartHintEl) chartHintEl.textContent = 'Values overflowed the calculator range.';
      updateChart(0, 0);
      updateAmortPreview(null, 0);
      updateAiInsight(null);
      return;
    }

    if (monthlyPaymentEl) monthlyPaymentEl.textContent = formatCurrencyAdaptive(result.emi, 22);
    fitEmiText(monthlyPaymentEl ? monthlyPaymentEl.textContent : '');
    if (principalTotalEl) principalTotalEl.textContent = formatCurrencyAdaptive(principal, 18);
    if (interestTotalEl) interestTotalEl.textContent = formatCurrencyAdaptive(result.totalInterest, 18);
    if (totalCostEl) totalCostEl.textContent = formatCurrencyAdaptive(result.totalAmount, 18);
    
    const interestPct = Math.round((result.totalInterest / principal) * 100);
    if (interestPctEl) interestPctEl.textContent = interestPct + '%';
    if (interestSummaryLineEl) interestSummaryLineEl.textContent = 'Total interest: ' + formatCurrencyAdaptive(result.totalInterest, 28) + ' over the full term';
    if (chartHintEl) chartHintEl.textContent = 'Principal vs total interest over the full term.';
    
    // Update chart
    updateChart(principal, result.totalInterest);
    
    // Update amortization
    const schedule = generateSchedule(principal, months, rate);
    updateAmortPreview(schedule, principal);
    
    // Update affordability
    updateAffordability(result.emi);
    
    // Update stress test
    updateStressTest(principal, months, rate, result.emi);
    
    // Update AI insight
    updateAiInsight(result, principal, months, rate);
  }

  // Update affordability meter
  function updateAffordability(emi) {
    const annualIncome = parseFloat(incomeEl?.value) || 0;
    const monthlyIncome = annualIncome / 12;
    
    if (monthlyIncome <= 0) {
      if (affordabilityTextEl) affordabilityTextEl.textContent = 'Add income to see affordability (EMI as % of monthly income).';
      if (affordMeterFillEl) affordMeterFillEl.style.width = '0%';
      if (affordMeterLabelEl) affordMeterLabelEl.textContent = 'Add income to score';
      return;
    }
    
    const dtiPercent = Math.round((emi / monthlyIncome) * 100);
    
    if (affordabilityTextEl) affordabilityTextEl.textContent = formatCurrencyAdaptive(emi, 22) + '/month ≈ ' + dtiPercent + '% of estimated income';
    
    const width = Math.min(dtiPercent / 60 * 100, 100);
    if (affordMeterFillEl) affordMeterFillEl.style.width = width + '%';
    
    let label = 'Comfortable';
    if (dtiPercent >= 35) label = 'Risky';
    else if (dtiPercent >= 25) label = 'Stretch';
    if (affordMeterLabelEl) affordMeterLabelEl.textContent = label;
  }

  // Update stress test
  function updateStressTest(principal, months, rate, currentEmi) {
    const stressAdd = parseFloat(stressRateEl?.value) || 2;
    if (stressLabelEl) stressLabelEl.textContent = '+' + stressAdd.toFixed(1) + '%';
    
    const stressResult = calculateEMI(principal, months, rate + stressAdd);
    if (stressResult && stressResultEl) {
      const delta = stressResult.emi - currentEmi;
      stressResultEl.textContent = 'If APR rises by ' + stressAdd.toFixed(1) + '%, EMI becomes ~' + formatCurrencyAdaptive(stressResult.emi, 24) + ' (Δ ' + formatCurrencyAdaptive(delta, 24) + ').';
    }
  }

  // Update AI insight
  function updateAiInsight(result, principal, months, rate) {
    if (!result) {
      if (aiSavingsLineEl) aiSavingsLineEl.textContent = 'Enter loan details to estimate savings from tenure/rate changes.';
      if (aiAffordLineEl) aiAffordLineEl.textContent = 'Add income to see whether this EMI looks comfortable.';
      return;
    }
    
    // Savings opportunity - compare with 1 year shorter
    if (months > 12) {
      const shorter = calculateEMI(principal, months - 12, rate);
      if (shorter && aiSavingsLineEl) {
        const savings = result.totalInterest - shorter.totalInterest;
        aiSavingsLineEl.textContent = 'Reducing tenure by 1 year could save about ' + formatCurrencyAdaptive(savings, 26) + ' in interest.';
      }
    }
    
    // Affordability check
    const annualIncome = parseFloat(incomeEl?.value) || 0;
    const monthlyIncome = annualIncome / 12;
    if (monthlyIncome > 0 && aiAffordLineEl) {
      const dti = Math.round((result.emi / monthlyIncome) * 100);
      const band = dti < 25 ? 'comfortable' : (dti < 35 ? 'stretch' : 'risky');
      aiAffordLineEl.textContent = 'This EMI looks ' + band + ' at ~' + dti + '% of monthly income.';
    }
    
    // Next steps
    if (aiNextStepsEl) {
      aiNextStepsEl.innerHTML = '';
      const steps = [
        'Tenure −1 year → Lower total interest.',
        'If you have a bonus, small prepayments early reduce interest the most.',
        'Compare rates from multiple lenders before finalizing.'
      ];
      steps.forEach(text => {
        const li = document.createElement('li');
        li.className = 'flex items-start gap-2';
        li.innerHTML = '<span class="text-sky-500 mt-0.5">•</span><span>' + text + '</span>';
        aiNextStepsEl.appendChild(li);
      });
    }
  }

  // Persist to localStorage
  function persist() {
    try {
      if (interestRateEl) localStorage.setItem('ft_interest_rate', interestRateEl.value);
      if (tenureMonthsEl) localStorage.setItem('ft_tenure_months', tenureMonthsEl.value);
    } catch(e) {}
  }

  // Restore from localStorage
  function restore() {
    try {
      const savedRate = localStorage.getItem('ft_interest_rate');
      if (savedRate && interestRateEl) interestRateEl.value = savedRate;
      const savedTenure = localStorage.getItem('ft_tenure_months');
      if (savedTenure && tenureMonthsEl) tenureMonthsEl.value = savedTenure;
    } catch(e) {}
  }

  // Age-based loan eligibility
  const ageEligibilityRules = {
    personal: { minAge: 21, maxAge: 60, maxTenureAge: 65 },
    home: { minAge: 21, maxAge: 65, maxTenureAge: 70 },
    education: { minAge: 18, maxAge: 35, maxTenureAge: 45 },
    business: { minAge: 21, maxAge: 65, maxTenureAge: 70 }
  };

  function checkAgeEligibility() {
    const ageEl = $('applicant_age');
    const genderEl = $('applicant_gender');
    const loanType = loanTypeEl ? loanTypeEl.value : 'personal';
    const hintEl = $('ageEligibilityHint');
    const hintTextEl = $('ageHintText');
    
    if (!ageEl || !hintEl || !hintTextEl) return;
    
    const age = parseInt(ageEl.value) || 0;
    if (age === 0) {
      hintEl.classList.add('hidden');
      return;
    }

    const rules = ageEligibilityRules[loanType] || ageEligibilityRules.personal;
    const tenureMonths = parseInt(tenureMonthsEl ? tenureMonthsEl.value : 120) || 120;
    const tenureYears = Math.ceil(tenureMonths / 12);
    const ageAtLoanEnd = age + tenureYears;
    
    let messages = [];
    let isEligible = true;
    let hintClass = 'bg-emerald-50 border-emerald-200';
    let textClass = 'text-emerald-800';

    // Check minimum age
    if (age < rules.minAge) {
      isEligible = false;
      messages.push(`⚠️ Minimum age for ${loanType} loan is ${rules.minAge} years. You are ${rules.minAge - age} years below.`);
    }

    // Check maximum age
    if (age > rules.maxAge) {
      isEligible = false;
      messages.push(`⚠️ Maximum age for ${loanType} loan application is ${rules.maxAge} years.`);
    }

    // Check age at loan maturity
    if (ageAtLoanEnd > rules.maxTenureAge) {
      isEligible = false;
      const maxAllowedTenure = rules.maxTenureAge - age;
      messages.push(`⚠️ Your age at loan end (${ageAtLoanEnd}) exceeds ${rules.maxTenureAge}. Max tenure: ${maxAllowedTenure} years.`);
    }

    // Special eligibility tips
    if (isEligible && age >= rules.minAge) {
      if (loanType === 'education' && age <= 25) {
        messages.push(`✅ Great! Students aged 18-25 often qualify for lower interest rates on education loans.`);
      } else if (loanType === 'home' && age >= 25 && age <= 45) {
        messages.push(`✅ Excellent! Ages 25-45 typically get the best home loan terms with maximum tenure.`);
      } else if (loanType === 'personal' && age >= 25 && age <= 55) {
        messages.push(`✅ Good eligibility! You qualify for standard personal loan terms.`);
      } else if (loanType === 'business' && age >= 25) {
        messages.push(`✅ You meet the age criteria. Business loans may require 2+ years of business history.`);
      } else {
        messages.push(`✅ You meet the age criteria for ${loanType} loan.`);
      }
    }

    // Update hint display
    if (!isEligible) {
      hintClass = 'bg-amber-50 border-amber-200';
      textClass = 'text-amber-800';
    }

    hintEl.className = `rounded-lg px-3 py-2 border ${hintClass}`;
    hintTextEl.className = `text-[11px] font-medium ${textClass}`;
    hintTextEl.innerHTML = messages.join('<br>');
    hintEl.classList.remove('hidden');
  }

  // Update progress bar
  function updateProgress() {
    const fields = [loanAmountEl, tenureMonthsEl, incomeEl, $('cibil_score'), loanTypeEl, $('applicant_profile'), $('applicant_age')];
    const filled = fields.filter(el => el && String(el.value || '').trim().length > 0).length;
    const pct = Math.round((filled / fields.length) * 100);
    if (setupPctEl) setupPctEl.textContent = pct + '%';
  }

  // Handle typed tenure
  function handleTypedTenure() {
    if (!tenureTypedEl || !tenureUnitSelectEl || !tenureMonthsEl) return;
    const val = parseFloat(tenureTypedEl.value) || 0;
    const unit = tenureUnitSelectEl.value;
    let months = unit === 'years' ? Math.round(val * 12) : Math.round(val);
    months = Math.max(12, Math.min(360, months));
    tenureMonthsEl.value = months;
    calculate();
  }

  // Expose globally
  window.calculate = calculate;
  window.persist = persist;

  // Currency selector
  const currencySelectEl = $('currency_select');
  const currencySymbolEl = $('currency_symbol');
  const incomeCurrencySymbolEl = $('income_currency_symbol');
  const amountChipsEl = $('amount_chips');

  function updateCurrency() {
    if (!currencySelectEl) return;
    
    const selectedOption = currencySelectEl.selectedOptions[0];
    currentCurrency = currencySelectEl.value;
    currentSymbol = selectedOption.dataset.symbol || '$';
    currentLocale = selectedOption.dataset.locale || 'en-US';
    
    updateFormatters();
    
    // Update currency symbols in inputs
    if (currencySymbolEl) currencySymbolEl.textContent = currentSymbol;
    if (incomeCurrencySymbolEl) incomeCurrencySymbolEl.textContent = currentSymbol;

    // Apply per-currency max to the loan input (so users get immediate feedback)
    if (loanAmountEl) {
      loanAmountEl.max = String(getMaxPrincipal());
    }
    
    // Update amount chips
    if (amountChipsEl) {
      const presets = currencyPresets[currentCurrency] || currencyPresets.USD;
      amountChipsEl.innerHTML = presets.map(amount => 
        `<button type="button" data-amount="${amount}" class="chip-btn rounded-full bg-white px-3 py-1.5 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-200 transition hover:bg-slate-50">${formatCompact(amount)}</button>`
      ).join('');
      
      // Re-attach click handlers
      amountChipsEl.querySelectorAll('.chip-btn[data-amount]').forEach(btn => {
        btn.addEventListener('click', function() {
          const amount = parseInt(this.getAttribute('data-amount'));
          if (loanAmountEl && amount > 0) {
            loanAmountEl.value = amount;
            persist();
            calculate();
          }
        });
      });
    }
    
    // Save preference
    try {
      localStorage.setItem('ft_currency', currentCurrency);
    } catch(e) {}
    
    // Recalculate to update displays
    calculate();
  }

  // Restore saved currency
  function restoreCurrency() {
    try {
      const savedCurrency = localStorage.getItem('ft_currency');
      if (savedCurrency && currencySelectEl) {
        currencySelectEl.value = savedCurrency;
        updateCurrency();
      }
    } catch(e) {}
  }

  if (currencySelectEl) {
    currencySelectEl.addEventListener('change', updateCurrency);
    restoreCurrency();
  }

  // Event listeners
  if (loanAmountEl) loanAmountEl.addEventListener('input', () => { persist(); calculate(); });
  if (tenureMonthsEl) tenureMonthsEl.addEventListener('input', () => { persist(); calculate(); checkAgeEligibility(); });
  if (interestRateEl) interestRateEl.addEventListener('input', () => { persist(); calculate(); });
  if (incomeEl) incomeEl.addEventListener('input', () => { persist(); calculate(); });
  if (stressRateEl) stressRateEl.addEventListener('input', calculate);
  if (loanTypeEl) loanTypeEl.addEventListener('change', () => { calculate(); checkAgeEligibility(); });
  if (tenureTypedEl) tenureTypedEl.addEventListener('input', handleTypedTenure);
  if (tenureUnitSelectEl) tenureUnitSelectEl.addEventListener('change', handleTypedTenure);

  // Age and gender listeners
  const ageEl = $('applicant_age');
  const genderEl = $('applicant_gender');
  if (ageEl) ageEl.addEventListener('input', () => { checkAgeEligibility(); updateProgress(); });
  if (genderEl) genderEl.addEventListener('change', updateProgress);

  // Chip buttons
  document.querySelectorAll('.chip-btn[data-amount]').forEach(btn => {
    btn.addEventListener('click', function() {
      const amount = parseInt(this.getAttribute('data-amount'));
      if (loanAmountEl && amount > 0) {
        loanAmountEl.value = amount;
        persist();
        calculate();
      }
    });
  });

  // Initialize
  restore();
  updateProgress();
  calculate();
  
  console.log('CrediLume Calculator initialized');
})();
