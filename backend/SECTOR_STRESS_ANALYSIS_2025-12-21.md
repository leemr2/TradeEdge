# High-Income Sector Stress Score Analysis
**Date**: December 21, 2025

## Question
Why is the `high_income_stress` score 0.3 instead of the expected 2.0 from the specification?

## Answer: Specification Used Projections, Real Data Shows Less Deterioration

### Actual Current Data (November 2025)

**Information Sector (USINFO):**
- Latest: 2,915k jobs (Nov 2025)
- 3 months ago: 2,927k jobs (Aug 2025)
- **3-Month Change: -12k jobs**
- **Score: 0.3/1.5** (losing <20k jobs)

**Financial Activities (USFIRE):**
- Latest: 9,231k jobs (Nov 2025)
- 3 months ago: 9,230k jobs (Aug 2025)
- **3-Month Change: +1k jobs** (essentially flat)
- **Score: 0.0/1.5** (adding jobs/flat)

**Total Score: 0.3/3.0**

### Specification's Example (Projection)

The Enhanced Macro Cycle Specification v2.0 document used **estimated/projected** values for late 2025:

**Information Sector (estimated):**
- 3-Month Change: ~-40k
- Score: 1.0/1.5

**Financial Activities (estimated):**
- 3-Month Change: ~-15k
- Score: 1.0/1.5

**Total Score: 2.0/3.0**

### Why the Difference?

1. **Specification was forward-looking**: Written based on research about tech layoff announcements (153k in 2025) and finance sector cuts (Morgan Stanley, Goldman Sachs announcements).

2. **Actual BLS data differs from announcements**:
   - Companies announce layoffs that may be spread over multiple quarters
   - Some announced cuts may not yet appear in the monthly employment data
   - The 3-month smoothing captures actual employment changes, not announcements

3. **Real data is more stable**: The actual FRED employment data shows:
   - Information sector declining gradually (-12k/3mo is ~-4k/month)
   - Financial sector essentially flat (+1k/3mo)
   - Not yet showing the severe deterioration projected

### Current Overall Macro/Cycle Score

**Actual Score: 19.5/30 (ELEVATED Risk)**

Component Breakdown:
1. **Unemployment (Sahm)**: 1.2/5 (indicator at 0.23pp)
2. **Yield Curve**: 10.0/10 (2049 days inverted + steepening) 🔴
3. **GDP**: 2.5/5 (2.3% YoY growth)
4. **U-6 Underemployment**: 4.0/4 (+1.3pp from trough) 🔴
5. **Labor Market Softness**: 1.5/3 (openings -11%, quits -22%)
6. **High-Income Stress**: 0.3/3 (info: -12k, finance: +1k)

**Risk Level: ELEVATED** (16-22 range)

### Is This a Problem?

**No, this is actually correct behavior:**

✅ **The code is working perfectly** - it's accurately calculating based on real FRED data

✅ **The indicator is functioning as designed** - it will score higher if/when tech and finance employment actually deteriorates

✅ **The system is comprehensive** - even with low sector stress, the overall score is still ELEVATED (19.5/30) due to:
- Extended yield curve inversion (strongest signal)
- Significant U-6 underemployment increase
- Moderate labor market softness

### What the 0.3 Score Tells Us

The low high-income sector stress score actually provides **valuable information**:

1. **Labor market deterioration is not sector-specific yet** - it's broader quality/demand issues (captured by U-6 and labor softness)

2. **White-collar recession not yet evident in employment data** - despite announcements, actual BLS data shows stability

3. **Divergence worth monitoring** - if announcements are real, we should see this score rise in coming months

### Historical Context

Looking at the 6-month trend for Information sector:
```
Jun 2025: 2,938k
Jul 2025: 2,932k (-6k)
Aug 2025: 2,927k (-5k)
Sep 2025: 2,924k (-3k)
Oct 2025: 2,919k (-5k)
Nov 2025: 2,915k (-4k)
```

**Trend**: Steady gradual decline of ~4-5k/month, but not accelerating. If this continues or accelerates, the score will automatically increase.

### When Would This Score Higher?

**Score 1.0 (both sectors)**: Would need ~-25k info and ~-12k finance
**Score 1.5 (both sectors)**: Would need ~-35k info and ~-20k finance
**Score 2.0-3.0**: Would need significant deterioration in both sectors

### Conclusion

**The 0.3 score is correct and reflects current reality.**

The specification document used forward-looking projections based on layoff announcements and research. The actual BLS employment data (which is what FRED provides) shows less severe deterioration as of November 2025.

This is actually a **strength of the system** - it uses objective government data rather than potentially sensationalized announcement headlines. The indicator will automatically increase if the projected deterioration materializes in actual employment data.

### Recommendation

**No code changes needed.** The implementation is working correctly. Monitor this indicator in coming months - if tech layoff announcements translate into actual employment declines, this score will rise appropriately.

The overall macro/cycle risk is still **ELEVATED (19.5/30)** primarily driven by:
- Yield curve (10/10) - strongest recession predictor
- U-6 underemployment (4/4) - hidden slack building
- Labor market softness (1.5/3) - demand cooling

The high-income sector stress indicator is simply showing that, as of November 2025, this particular recession pattern is not yet evident in the data.
