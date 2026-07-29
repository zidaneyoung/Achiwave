param(
    [Parameter(Mandatory = $true)]
    [string]$Repo,

    [Parameter(Mandatory = $true)]
    [string]$Owner,

    [Parameter(Mandatory = $true)]
    [int]$ProjectNumber
)

$ErrorActionPreference = "Stop"

$project = gh project view $ProjectNumber --owner $Owner --format json | ConvertFrom-Json
$projectId = $project.id

gh project edit $ProjectNumber --owner $Owner --title "Achiwave Development" --description "Native iOS and Android application development board for Achiwave." | Out-Null
gh project link $ProjectNumber --owner $Owner --repo $Repo | Out-Null

$fields = gh project field-list $ProjectNumber --owner $Owner --format json --limit 100 | ConvertFrom-Json
$existingStage = $fields.fields | Where-Object { $_.name -eq "Stage" } | Select-Object -First 1
if ($existingStage) {
    gh project field-delete --id $existingStage.id | Out-Null
}

$stageOptions = @(
    "Stage 1 - Product Rules and Domain Foundation",
    "Stage 2 - Mobile and Backend Application Foundation",
    "Stage 3 - Database Schema and Data Integrity",
    "Stage 4 - Mobile Authentication and Device Security",
    "Stage 5 - Native Mobile Design System and Navigation",
    "Stage 6 - Campaign and Quest Management",
    "Stage 7 - Quest Completion and Synchronization",
    "Stage 8 - XP, Levels and Streaks",
    "Stage 9 - Achievement Rules Engine",
    "Stage 10 - Native Achievement Unlock Experience",
    "Stage 11 - Recurring Quests and Mobile Notifications",
    "Stage 12 - Mobile Dashboard and Analytics",
    "Stage 13 - Evidence and Native Device Features",
    "Stage 14 - Mobile Security and Reliability",
    "Stage 15 - Native Mobile Testing and Acceptance Audit",
    "Stage 16 - App Store and Play Store Release"
)

$stageOptionInput = @()
foreach ($stageOption in $stageOptions) {
    $stageOptionInput += @{
        name = $stageOption
        color = "BLUE"
        description = $stageOption
    }
}

$createStageMutation = @'
mutation($input: CreateProjectV2FieldInput!) {
  createProjectV2Field(input: $input) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
      }
    }
  }
}
'@

@{
    query = $createStageMutation
    variables = @{
        input = @{
            projectId = $projectId
            dataType = "SINGLE_SELECT"
            name = "Stage"
            singleSelectOptions = $stageOptionInput
        }
    }
} | ConvertTo-Json -Depth 10 -Compress | gh api graphql --input - | Out-Null

$fields = gh project field-list $ProjectNumber --owner $Owner --format json --limit 100 | ConvertFrom-Json
$statusField = $fields.fields | Where-Object { $_.name -eq "Status" } | Select-Object -First 1
$stageField = $fields.fields | Where-Object { $_.name -eq "Stage" } | Select-Object -First 1
$backlogOption = $statusField.options | Where-Object { $_.name -eq "Backlog" } | Select-Object -First 1

if (-not $statusField -or -not $stageField -or -not $backlogOption) {
    throw "Required project fields were not found."
}

$stageOptionByName = @{}
foreach ($option in $stageField.options) {
    $stageOptionByName[$option.name] = $option.id
}

$existingItems = gh project item-list $ProjectNumber --owner $Owner --format json --limit 200 | ConvertFrom-Json
$itemIdByUrl = @{}
foreach ($existingItem in $existingItems.items) {
    if ($existingItem.content -and $existingItem.content.url) {
        $itemIdByUrl[$existingItem.content.url] = $existingItem.id
    }
}

$issues = gh issue list --repo $Repo --state open --limit 100 --json number,title,url,milestone | ConvertFrom-Json
$issues = $issues | Sort-Object number

foreach ($issue in $issues) {
    if ($itemIdByUrl.ContainsKey($issue.url)) {
        $itemId = $itemIdByUrl[$issue.url]
    } else {
        $item = gh project item-add $ProjectNumber --owner $Owner --url $issue.url --format json | ConvertFrom-Json
        $itemId = $item.id
    }

    gh project item-edit --id $itemId --project-id $projectId --field-id $statusField.id --single-select-option-id $backlogOption.id | Out-Null

    $stageName = $issue.milestone.title
    if ($stageOptionByName.ContainsKey($stageName)) {
        gh project item-edit --id $itemId --project-id $projectId --field-id $stageField.id --single-select-option-id $stageOptionByName[$stageName] | Out-Null
    } else {
        Write-Warning "No Stage option found for issue #$($issue.number): $stageName"
    }
}

Write-Output "Configured project $ProjectNumber with $($issues.Count) Achiwave issues."
