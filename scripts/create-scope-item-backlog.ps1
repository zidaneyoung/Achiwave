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

$milestones = gh api "repos/$Repo/milestones?state=open&per_page=100" | ConvertFrom-Json
$milestoneByTitle = @{}
foreach ($milestone in $milestones) {
    $milestoneByTitle[$milestone.title] = $milestone.number
}

function Get-Labels {
    param([string]$Text)

    $labels = New-Object System.Collections.Generic.HashSet[string]
    [void]$labels.Add("mobile")

    if ($Text -match "document|define|description|privacy disclosures|permission explanations|architecture|known limitations|guideline|rules") { [void]$labels.Add("documentation") }
    if ($Text -match "React Native|Expo|Router|screen|navigation|form|button|card|list|theme|typography|dashboard|chart|animation|haptic|audio|share sheet|camera|photo|library|keyboard|safe-area|touch|bottom|modal|UI|application starts|indicator|presentation") { [void]$labels.Add("frontend") }
    if ($Text -match "FastAPI|backend|API|server|endpoint|REST|WebSocket|SSE|authoritative|recurring|XP|level|streak|achievement|quest-completion validation|scheduler|rate limiting") { [void]$labels.Add("backend") }
    if ($Text -match "PostgreSQL|database|SQLAlchemy|Alembic|migration|schema|SQLite|local database|persistence|RegisteredDevice|PushToken|SynchronizationOperation|ClientMutation|DeviceSession|NotificationDelivery") { [void]$labels.Add("database") }
    if ($Text -match "Redis|Celery|worker|scheduler|Beat|background|schedule|recurring|reminder event") { [void]$labels.Add("worker") }
    if ($Text -match "auth|credential|secure|secret|token|session|biometric|permission|privacy|HTTPS|certificate|deep-link|deep link|log|redaction|clipboard|screenshot|rooted|compromised|rate limiting|logout|reinstall|account-switching|transport|signing") { [void]$labels.Add("security") }
    if ($Text -match "notification|push|reminder|Notify|Expo Notifications|token|permission state|local notification|remote push") { [void]$labels.Add("notifications") }
    if ($Text -match "offline|synchron|sync|queue|conflict|duplicate|client mutation|multiple device|reconnection|retry|pending|replayed|clock|timezone") { [void]$labels.Add("synchronization") }
    if ($Text -match "test|verify|audit|acceptance|physical|Playwright|low-performance|screen reader|large font|reduced motion|internal release verification") { [void]$labels.Add("testing") }
    if ($Text -match "environment|Docker|Compose|Redis|build|EAS|identifier|bundle|configuration|production|monitoring|crash reporting|infrastructure|development build|local development|health|readiness") { [void]$labels.Add("infrastructure") }
    if ($Text -match "App Store|Play Store|store|release|submit|signed|beta|testing track|screenshots|metadata|icons|splash|archive|App Bundle") { [void]$labels.Add("release") }

    return [string[]]$labels
}

function New-Body {
    param(
        [string]$Stage,
        [string]$Item,
        [string]$StageObjective,
        [string[]]$Acceptance,
        [string[]]$Dependencies,
        [string[]]$OutOfScope
    )

    $lines = @(
        "Objective",
        "$Item.",
        "",
        "Stage",
        $Stage,
        "",
        "Stage Objective",
        $StageObjective,
        "",
        "Scope",
        "1. $Item.",
        "",
        "Acceptance Criteria"
    )

    for ($i = 0; $i -lt $Acceptance.Count; $i++) {
        $lines += "$($i + 1). $($Acceptance[$i])"
    }

    $lines += @("", "Dependencies")
    for ($i = 0; $i -lt $Dependencies.Count; $i++) {
        $lines += "$($i + 1). $($Dependencies[$i])"
    }

    $lines += @("", "Out of Scope")
    for ($i = 0; $i -lt $OutOfScope.Count; $i++) {
        $lines += "$($i + 1). $($OutOfScope[$i])"
    }

    return ($lines -join "`n")
}

$stages = @(
    @{
        title = "Stage 1 - Product Rules and Domain Foundation"
        objective = "Document the product and domain rules that keep progression server-authoritative and safe across mobile edge cases."
        dependencies = @("None.")
        out = @("Feature implementation.", "Mobile UI implementation.", "Store submission.")
        acceptance = @("The server timestamp is authoritative for progression calculations.", "Device clock changes cannot independently manipulate XP or streaks.", "Duplicate offline submissions cannot create duplicate completions.", "Conflict-resolution behavior is documented.", "Notification permission is optional.", "Denying notifications does not prevent normal application use.", "Multiple devices can synchronize without duplicating rewards.")
        items = @("Document offline quest completion rules", "Document synchronization conflict behavior", "Document device timezone change behavior", "Document notification permission denial behavior", "Document multiple-device account behavior", "Document achievement unlock behavior while the app is closed", "Document achievement presentation after reconnection", "Document device clock manipulation behavior", "Document local versus server timestamp behavior")
    },
    @{
        title = "Stage 2 - Mobile and Backend Application Foundation"
        objective = "Create the React Native mobile application, backend services, and local development environment."
        dependencies = @("Stage 1 product and domain rules are documented.")
        out = @("Web frontend.", "Browser support.", "Responsive desktop layouts.", "Production store submission.", "Achievement features.", "Offline synchronization.")
        acceptance = @("The application starts on an Android emulator.", "The application starts on a physical Android device.", "The application can produce an Android development build.", "The application configuration supports an iOS development build.", "An iOS build can be produced through the selected build service.", "Navigation works without a browser.", "The mobile application can reach the backend API.", "PostgreSQL accepts backend connections.", "Redis accepts backend and worker connections.", "The worker starts successfully.", "The scheduler starts successfully.", "Database migrations apply successfully.", "Android and iOS use distinct valid application identifiers.", "Development and production API URLs are configurable.", "Secrets are not embedded in the mobile bundle.", "The application handles backend unavailability without crashing.")
        items = @("Create the React Native and Expo application", "Configure TypeScript", "Configure Expo Router", "Configure Android application identifiers", "Configure iOS bundle identifiers", "Create the FastAPI backend", "Configure PostgreSQL", "Configure Redis", "Configure Celery worker and scheduler", "Configure database migrations", "Configure environment variables", "Create API health and readiness endpoints", "Configure Android development builds", "Configure iOS development builds", "Configure mobile API environments", "Add structured backend logging", "Add mobile error boundaries", "Add environment-specific application configuration")
    },
    @{
        title = "Stage 3 - Database Schema and Data Integrity"
        objective = "Create the database schema and integrity rules required by the mobile and backend platform."
        dependencies = @("Stage 2 backend foundation and migrations are available.")
        out = @("Push delivery integration.", "Mobile UI implementation.", "Achievement presentation.")
        acceptance = @("Push tokens are associated with the correct user and device.", "Invalidated push tokens can be deactivated.", "Duplicate client mutation identifiers are rejected.", "A synchronization operation cannot affect another user's records.", "Device removal invalidates the associated session where required.", "Notification delivery attempts are auditable.")
        items = @("Add RegisteredDevice schema support", "Add PushToken schema support", "Add SynchronizationOperation schema support", "Add ClientMutation schema support", "Add DeviceSession schema support", "Add NotificationDelivery schema support")
    },
    @{
        title = "Stage 4 - Mobile Authentication and Device Security"
        objective = "Implement secure mobile authentication and protected local credential storage."
        dependencies = @("Stage 3 device and session schema support exists.")
        out = @("Browser cookies.", "Web sessions.", "Enterprise single sign-on.", "Mandatory biometrics.", "Passwordless authentication in the initial release.")
        acceptance = @("A valid user can register.", "A valid user can sign in.", "Invalid credentials produce a controlled error.", "Authentication secrets are not stored in ordinary unencrypted application storage.", "Secure local values use the platform-supported secure-storage mechanism.", "Signing out removes or invalidates local authentication data.", "Protected screens cannot be opened without a valid session.", "Expired sessions trigger a controlled reauthentication flow.", "Device sessions can be invalidated from the backend.", "Biometric access does not replace backend authentication.", "Sensitive authentication data is excluded from logs.", "Offline launch follows documented session behavior.", "Another user cannot recover the previous user's cached private data.")
        items = @("Register users", "Sign users in", "Sign users out", "Refresh authenticated sessions", "Store supported credentials securely", "Protect authenticated routes", "Handle expired sessions", "Revoke device sessions", "Support account deactivation", "Add optional biometric re-entry after initial authentication", "Prevent sensitive values from appearing in logs", "Clear protected local data after logout", "Handle authentication while offline", "Handle token refresh failure")
    },
    @{
        title = "Stage 5 - Native Mobile Design System and Navigation"
        objective = "Create an accessible mobile design system and navigation structure for Android and iOS."
        dependencies = @("Stage 2 mobile application foundation exists.")
        out = @("Web navigation.", "Sidebars.", "Mouse-specific interaction.", "Desktop breakpoints.", "Browser keyboard shortcuts.")
        acceptance = @("Navigation works on Android and iOS builds.", "Android system-back behavior is predictable.", "Screens respect safe areas.", "Forms remain usable when the software keyboard is visible.", "Primary touch targets are sufficiently large and separated.", "Screen-reader labels identify interactive controls.", "Application text responds appropriately to supported system font scaling.", "Status is not communicated through color alone.", "Reduced-motion preferences disable nonessential animation.", "Light and dark themes remain readable.", "Loading, empty, error, and offline states are distinguishable.", "Navigation state survives supported application lifecycle transitions.", "No workflow depends on hover behavior.", "No screen requires a desktop viewport.")
        items = @("Create bottom-tab navigation", "Create stack navigation", "Create modal navigation", "Add safe-area handling", "Add keyboard avoidance", "Add Android back-button handling", "Add light and dark themes", "Add native form controls", "Add buttons and touch states", "Add cards and list items", "Add bottom sheets where appropriate", "Add loading skeletons", "Add empty states", "Add error states", "Add offline indicators", "Add synchronization indicators", "Add accessible labels and roles", "Add scalable typography support", "Add reduced-motion support", "Add touch-target standards", "Add screen-reader testing requirements")
    },
    @{
        title = "Stage 6 - Campaign and Quest Management"
        objective = "Build native campaign and quest management workflows for mobile users."
        dependencies = @("Stage 5 design system and navigation are available.")
        out = @("Web interface requirements.", "Desktop campaign or quest UI.", "Fully offline editing for all data types.")
        acceptance = @("Campaigns can be created using the on-screen keyboard.", "Creation forms remain visible while the keyboard is open.", "Pull-to-refresh synchronizes server data.", "Swipe actions have visible non-swipe alternatives.", "Date selectors behave correctly on Android and iOS.", "Unsaved form changes are protected from accidental dismissal.", "Lists remain usable with representative portfolio data volumes.")
        items = @("Create native campaign lists", "Create native quest lists", "Add swipe actions only when accessible alternatives exist", "Add pull-to-refresh", "Add mobile date and time pickers", "Add bottom-sheet or modal creation flows", "Add touch-friendly filtering", "Add native confirmation prompts")
    },
    @{
        title = "Stage 7 - Quest Completion and Synchronization"
        objective = "Support reliable quest completion under online and controlled offline conditions."
        dependencies = @("Stage 6 quest management workflows exist.", "Stage 3 synchronization data model exists.")
        out = @("Fully offline account creation.", "Peer-to-peer synchronization.", "Unlimited offline history.", "Editing all data types while offline.", "Device-authoritative progression.")
        acceptance = @("Online completion is persisted by the backend.", "Rapid repeated taps do not create duplicate completions.", "Offline completion creates a clearly identified pending operation.", "Pending operations survive supported application restarts.", "Reconnection attempts synchronization.", "Replayed operations cannot award duplicate XP.", "Permanent validation failures are shown to the user.", "Recoverable failures can be retried.", "Server rejection restores the correct interface state.", "A completion made on another device appears after synchronization.", "Device time does not determine authoritative XP or streak results.", "Pending, synchronized, and failed states are visually distinguishable.", "Logging out safely handles or removes queued private operations.")
        items = @("Complete quests while online", "Optimistically update supported interface states", "Roll back invalid optimistic changes", "Queue supported completions while offline", "Assign unique client mutation identifiers", "Synchronize queued completions", "Prevent duplicate submissions", "Handle synchronization conflicts", "Display synchronization status", "Retry recoverable failures", "Stop retrying permanent failures", "Provide a manual retry action", "Preserve server authority", "Support multiple devices")
    },
    @{
        title = "Stage 8 - XP, Levels and Streaks"
        objective = "Keep XP, levels, and streaks server-authoritative while presenting synchronized mobile feedback."
        dependencies = @("Stage 7 quest completion and synchronization are reliable.")
        out = @("Achievement unlock presentation.", "Client-authoritative progression.", "Desktop analytics.")
        acceptance = @("XP displayed by the device matches the server ledger after synchronization.", "Haptic feedback can be disabled where appropriate.", "XP animation does not run before server confirmation unless explicitly presented as pending.", "Level-up events are not presented repeatedly after application restart.", "Streak values remain server-authoritative.")
        items = @("Add XP gain animation", "Add level-progress bar", "Add streak indicator", "Add haptic feedback", "Add synchronized totals", "Add offline pending state")
    },
    @{
        title = "Stage 9 - Achievement Rules Engine"
        objective = "Keep achievement evaluation on the backend and render server-provided achievement state on mobile."
        dependencies = @("Stage 8 XP, level, and streak processing exists.")
        out = @("Device-side achievement awarding.", "Client-trusted achievement rules.", "Native unlock presentation.")
        acceptance = @("The mobile application cannot directly award an achievement.", "Achievement progress received from the server is rendered correctly.", "Hidden achievement conditions remain concealed.", "Rules and internal evaluation details are not trusted from editable client state.", "Offline completion can trigger an achievement only after server synchronization.")
        items = @("Render server-provided achievement progress", "Conceal hidden achievement conditions", "Prevent direct mobile achievement awards", "Keep rules and internal evaluation details untrusted from client state", "Trigger offline-completion achievements only after server synchronization")
    },
    @{
        title = "Stage 10 - Native Achievement Unlock Experience"
        objective = "Create a distinctive mobile reward experience using native audio, animation, haptic feedback, and notifications."
        dependencies = @("Stage 9 backend achievement engine and mobile achievement rendering exist.")
        out = @("Steam sound assets.", "Steam iconography.", "Steam branding.", "Custom user-uploaded sounds.", "Critical-alert permissions.", "Promotional notification spam.")
        acceptance = @("An achievement unlock is first persisted by the backend.", "A foregrounded application receives the unlock.", "A backgrounded application can receive a push notification when platform delivery succeeds.", "Tapping a notification opens the correct achievement.", "An original or properly licensed sound is used.", "Sound can be disabled.", "Haptic feedback can be disabled where supported.", "Reduced-motion mode presents an accessible alternative.", "The unlock remains understandable without sound.", "The unlock remains understandable without animation.", "Duplicate push delivery does not create duplicate achievements.", "A previously acknowledged unlock is not repeatedly presented.", "Notification denial does not block achievement access inside the application.", "Missed unlocks remain available in notification history.", "The experience works on both Android and iOS builds.")
        items = @("Receive achievement-unlock events while the app is open", "Receive push notifications while the app is backgrounded or closed", "Display an in-app achievement banner", "Display a full achievement-unlock presentation", "Play an original achievement sound", "Trigger configurable haptic feedback", "Respect device silent behavior where required", "Respect application sound settings", "Respect reduced-motion settings", "Prevent duplicate presentations", "Store unread unlock notifications", "Deep-link notifications to achievement details", "Handle unlocks received on multiple devices", "Handle notification permission denial", "Provide an accessible non-audio equivalent")
    },
    @{
        title = "Stage 11 - Recurring Quests and Mobile Notifications"
        objective = "Generate recurring quests on the backend and notify users through platform-native notifications."
        dependencies = @("Stage 6 quest management exists.", "Stage 3 device and push-token schema exists.")
        out = @("Dependence on continuously running mobile background timers.", "SMS reminders.", "Email reminders.", "Location-triggered reminders.", "Alarm-clock functionality.")
        acceptance = @("Recurring occurrences are generated without the application being open.", "Closing the mobile application does not stop backend recurrence processing.", "Exact progression logic does not depend on mobile background execution.", "A valid device can register for notifications.", "Permission is requested in context rather than immediately without explanation.", "A reminder opens the related quest.", "Duplicate scheduler execution does not produce duplicate occurrences.", "Invalid device tokens are handled.", "Disabled notification categories are respected.", "Timezone changes update future reminder behavior.", "Historical completions retain their original authoritative timestamps.", "Users without notification permission can still view upcoming quests in the application.")
        items = @("Generate recurring quest occurrences on the backend", "Schedule reminder events on the backend", "Register device push tokens", "Send remote push notifications", "Schedule appropriate local notifications", "Cancel outdated local notifications", "Handle changed recurrence schedules", "Handle timezone changes", "Handle notification permission state", "Open the relevant quest from a notification", "Deactivate invalid push tokens", "Prevent duplicate reminders", "Display notification settings")
    },
    @{
        title = "Stage 12 - Mobile Dashboard and Analytics"
        objective = "Replace desktop analytics with mobile-readable dashboard and progress views."
        dependencies = @("Stage 8 progression data exists.", "Stage 9 achievement progress exists.")
        out = @("Desktop charts.", "Dense tables.", "Hover-only chart inspection.", "Horizontal desktop layouts.")
        acceptance = @("Analytics are readable on supported phone sizes.", "Charts do not require hover interaction.", "Chart values can be inspected using touch and accessible alternatives.", "The dashboard does not depend on horizontal desktop layouts.", "Long lists use appropriate mobile rendering and pagination strategies.", "Pull-to-refresh updates the dashboard.", "Cached data is clearly distinguished when synchronization is unavailable.")
        items = @("Add mobile summary cards", "Add swipeable or vertically stacked analytics", "Add touch-accessible date filters", "Add campaign progress rings or bars", "Add achievement collection grids", "Add streak calendars", "Add weekly summaries", "Add scrollable charts", "Add reduced-data summaries for small displays")
    },
    @{
        title = "Stage 13 - Evidence and Native Device Features"
        objective = "Add evidence capture, uploads, sharing, and native permission handling."
        dependencies = @("Stage 6 quest management exists.", "Stage 4 authentication and privacy boundaries exist.")
        out = @("Public evidence galleries.", "Unrestricted file uploads.", "Social-network API posting.", "Custom user-designed share templates.")
        acceptance = @("Camera access is requested only when the user selects camera capture.", "Media-library access is requested only when required.", "Denying permission does not crash the application.", "The user receives an alternative when a permission is denied.", "Unsupported files are rejected.", "Oversized files are rejected or safely compressed according to documented rules.", "Upload progress is visible.", "Failed uploads can be retried.", "Private evidence cannot be accessed publicly.", "Shared achievement images use only approved information.", "Native sharing works on supported Android and iOS devices.", "Temporary sensitive files are not retained unnecessarily.")
        items = @("Capture evidence using the device camera", "Select evidence from the photo library", "Select supported documents", "Compress images where appropriate", "Upload evidence securely", "Display upload progress", "Retry failed uploads", "Remove local temporary files", "Generate shareable achievement images", "Open the native share sheet", "Control evidence privacy", "Request device permissions only when required")
    },
    @{
        title = "Stage 14 - Mobile Security and Reliability"
        objective = "Harden mobile-specific security and reliability behavior."
        dependencies = @("Stage 4 authentication exists.", "Stage 7 synchronization exists.", "Stage 11 notification handling exists.")
        out = @("Formal penetration testing.", "Enterprise mobile device management.", "Guaranteed support on rooted or compromised devices.")
        acceptance = @("Private values do not appear in notification previews unless explicitly appropriate.", "Deep links validate authentication and resource ownership.", "Sensitive tokens do not appear in logs.", "Logout clears protected cached data.", "Local databases do not store unnecessary secrets.", "Reinstall and account-switching behavior is documented.", "Invalid deep links fail safely.", "Network interruption does not corrupt local synchronization state.", "The application uses encrypted HTTPS communication in production.", "Production configuration excludes development API endpoints.")
        items = @("Add secure token storage requirements", "Configure certificate and transport security", "Review sensitive screenshot behavior", "Review clipboard-data handling", "Validate deep links", "Protect notification-content privacy", "Document rooted or compromised-device limitations", "Add log redaction", "Protect local database storage", "Remove cache after logout", "Invalidate push tokens", "Add API rate limiting", "Protect offline queue integrity", "Test application lifecycle behavior")
    },
    @{
        title = "Stage 15 - Native Mobile Testing and Acceptance Audit"
        objective = "Verify native Android and iOS behavior before release."
        dependencies = @("Primary MVP functional flow is complete.")
        out = @("Production store submission.", "External QA vendor process.", "Formal certification.")
        acceptance = @("Critical workflows pass on Android.", "Critical workflows pass on iOS.", "At least one physical device from each supported platform is tested.", "Quest completion survives expected lifecycle transitions.", "Offline synchronization does not duplicate progress.", "Push notification deep links work.", "Notification denial is handled.", "Camera and media permission denial are handled.", "Achievement audio can be disabled.", "Achievement haptics can be disabled where supported.", "Reduced-motion behavior is verified.", "Large-text layouts remain usable.", "Screen-reader navigation is verified.", "Session expiration produces a controlled result.", "The application recovers from backend unavailability.", "No criterion is marked passed without evidence.")
        items = @("Unit-test domain and mobile presentation logic", "Integration-test API communication", "Test Android navigation", "Test iOS navigation", "Test physical Android devices", "Test physical iOS devices", "Test application backgrounding", "Test application termination and reopening", "Test offline and reconnection flows", "Test push notifications", "Test deep links", "Test audio and haptics", "Test reduced motion", "Test large font sizes", "Test screen readers", "Test keyboard interaction", "Test permission denial", "Test session expiration", "Test app-version upgrades", "Test representative low-performance devices")
    },
    @{
        title = "Stage 16 - App Store and Play Store Release"
        objective = "Produce signed Android and iOS builds and prepare the application for store distribution."
        dependencies = @("Stage 15 native mobile testing and acceptance audit is complete.")
        out = @("Web deployment.", "Browser compatibility.", "GitHub configuration.", "GitHub Actions.", "Tablet-specific redesign in the initial release.", "Apple Watch application.", "Wear OS application.", "Desktop application.")
        acceptance = @("A signed Android App Bundle is generated.", "A signed iOS application archive is generated.", "The Android application installs through a testing track.", "The iOS application installs through the selected beta-distribution process.", "Application identifiers match production configuration.", "Store screenshots represent the actual application.", "Privacy disclosures correspond to actual data processing.", "Permission descriptions correspond to implemented functionality.", "The application passes internal release verification.", "Production API endpoints use HTTPS.", "Crash reporting receives a controlled test event.", "Push notifications work with production credentials.", "No development credentials are included.", "No unfinished controls appear operational.", "Store metadata does not claim Steam affiliation.", "The application is reviewed against current Apple and Google requirements before submission.")
        items = @("Configure production application identifiers", "Configure Android signing", "Configure iOS signing", "Create production builds", "Create application icons", "Create splash screens", "Prepare store screenshots", "Prepare store descriptions", "Prepare privacy disclosures", "Prepare permission explanations", "Configure internal testing", "Configure iOS beta testing", "Configure Android testing tracks", "Submit release candidates", "Resolve store-review defects", "Add production monitoring", "Add crash reporting", "Seed a demonstration account where appropriate", "Record a mobile demonstration video", "Document known limitations", "Create architecture and synchronization diagrams")
    }
)

$oldIssues = gh issue list --repo $Repo --state open --limit 200 --json number,title,url | ConvertFrom-Json
$oldIssues = $oldIssues | Where-Object { $_.number -le 32 }
foreach ($issue in $oldIssues) {
    gh issue close $issue.number --repo $Repo --reason "not planned" --comment "Replaced by granular scope-item issues generated from the native mobile application direction." | Out-Null
}

$projectItems = gh project item-list $ProjectNumber --owner $Owner --format json --limit 300 | ConvertFrom-Json
foreach ($item in $projectItems.items) {
    if ($item.content -and $item.content.repository -eq $Repo -and $item.content.number -le 32) {
        gh project item-archive $ProjectNumber --owner $Owner --id $item.id | Out-Null
    }
}

$existingIssues = gh issue list --repo $Repo --state all --limit 500 --json title,url | ConvertFrom-Json
$existingByTitle = @{}
foreach ($issue in $existingIssues) {
    $existingByTitle[$issue.title] = $issue.url
}

foreach ($stage in $stages) {
    if (-not $milestoneByTitle.ContainsKey($stage.title)) {
        throw "Missing milestone: $($stage.title)"
    }

    foreach ($item in $stage.items) {
        $title = "$($stage.title): $item"
        $labels = Get-Labels "$($stage.title) $item"
        $body = New-Body -Stage $stage.title -Item $item -StageObjective $stage.objective -Acceptance $stage.acceptance -Dependencies $stage.dependencies -OutOfScope $stage.out

        if ($existingByTitle.ContainsKey($title)) {
            $issueUrl = $existingByTitle[$title]
        } else {
            $labelArg = $labels -join ","
            $issueUrl = gh issue create --repo $Repo --title $title --body $body --label $labelArg --milestone $stage.title
            $existingByTitle[$title] = $issueUrl
        }

        $addedItem = gh project item-add $ProjectNumber --owner $Owner --url $issueUrl --format json | ConvertFrom-Json
        gh project item-edit --id $addedItem.id --project-id $projectId --field-id $statusField.id --single-select-option-id $backlogOption.id | Out-Null

        if ($stageOptionByName.ContainsKey($stage.title)) {
            gh project item-edit --id $addedItem.id --project-id $projectId --field-id $stageField.id --single-select-option-id $stageOptionByName[$stage.title] | Out-Null
        }
    }
}

$createdCount = ($stages | ForEach-Object { $_.items.Count } | Measure-Object -Sum).Sum
Write-Output "Scope-item backlog configured with $createdCount granular issues."
