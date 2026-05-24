$url = "https://tanhdev.com/"
$apiUrl = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed?url=$url&category=PERFORMANCE&category=ACCESSIBILITY&category=BEST_PRACTICES&category=SEO&strategy=mobile"
$response = Invoke-RestMethod -Uri $apiUrl
$performance = $response.lighthouseResult.categories.performance.score * 100
$accessibility = $response.lighthouseResult.categories.accessibility.score * 100
$bestPractices = $response.lighthouseResult.categories.'best-practices'.score * 100
$seo = $response.lighthouseResult.categories.seo.score * 100

Write-Output "Mobile Scores:"
Write-Output "Performance: $performance"
Write-Output "Accessibility: $accessibility"
Write-Output "Best Practices: $bestPractices"
Write-Output "SEO: $seo"

$apiUrlDesktop = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed?url=$url&category=PERFORMANCE&category=ACCESSIBILITY&category=BEST_PRACTICES&category=SEO&strategy=desktop"
$responseDesktop = Invoke-RestMethod -Uri $apiUrlDesktop
$performanceD = $responseDesktop.lighthouseResult.categories.performance.score * 100
$accessibilityD = $responseDesktop.lighthouseResult.categories.accessibility.score * 100
$bestPracticesD = $responseDesktop.lighthouseResult.categories.'best-practices'.score * 100
$seoD = $responseDesktop.lighthouseResult.categories.seo.score * 100

Write-Output "Desktop Scores:"
Write-Output "Performance: $performanceD"
Write-Output "Accessibility: $accessibilityD"
Write-Output "Best Practices: $bestPracticesD"
Write-Output "SEO: $seoD"
