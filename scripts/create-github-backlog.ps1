param(
    [Parameter(Mandatory = $true)]
    [string]$Repo
)

$ErrorActionPreference = "Stop"

$labels = @(
    @{ name = "documentation"; color = "0969DA"; description = "Product rules, architecture notes, setup, and release documentation" },
    @{ name = "frontend"; color = "2DA44E"; description = "React Native screens, navigation, forms, and client behavior" },
    @{ name = "backend"; color = "8250DF"; description = "FastAPI endpoints and application logic" },
    @{ name = "database"; color = "D4A72C"; description = "PostgreSQL tables, migrations, models, and data integrity" },
    @{ name = "worker"; color = "1F6FEB"; description = "Celery workers, scheduler, recurrence, and background processing" },
    @{ name = "security"; color = "CF222E"; description = "Authentication, authorization, secure storage, validation, and privacy" },
    @{ name = "testing"; color = "0E8A8A"; description = "Unit, integration, device, and release acceptance tests" },
    @{ name = "infrastructure"; color = "BC4C00"; description = "Docker, Redis, build pipelines, environments, and deployment configuration" },
    @{ name = "mobile"; color = "54AEFF"; description = "iOS and Android native application capabilities" },
    @{ name = "notifications"; color = "FBCA04"; description = "Push notifications, local notifications, delivery, and deep links" },
    @{ name = "synchronization"; color = "5319E7"; description = "Offline queueing, idempotency, conflict handling, and multi-device sync" },
    @{ name = "release"; color = "B60205"; description = "App Store, Play Store, signing, beta, and production release work" }
)

foreach ($label in $labels) {
    gh label create $label.name --repo $Repo --color $label.color --description $label.description --force | Out-Null
}

$stages = @(
    @{ title = "Stage 1 - Product Rules and Domain Foundation"; description = "Product rules, server-authoritative progression, and mobile edge cases." },
    @{ title = "Stage 2 - Mobile and Backend Application Foundation"; description = "React Native app, FastAPI services, and local development environment." },
    @{ title = "Stage 3 - Database Schema and Data Integrity"; description = "Core schema, device records, sync operations, and auditable delivery data." },
    @{ title = "Stage 4 - Mobile Authentication and Device Security"; description = "Secure mobile authentication, session refresh, protected routes, and local credential storage." },
    @{ title = "Stage 5 - Native Mobile Design System and Navigation"; description = "Accessible iOS and Android design system, navigation, themes, and lifecycle behavior." },
    @{ title = "Stage 6 - Campaign and Quest Management"; description = "Native campaign and quest creation, lists, filtering, and editing flows." },
    @{ title = "Stage 7 - Quest Completion and Synchronization"; description = "Reliable online and controlled offline quest completion with server authority." },
    @{ title = "Stage 8 - XP, Levels and Streaks"; description = "Server-authoritative XP, level, and streak processing with mobile presentation." },
    @{ title = "Stage 9 - Achievement Rules Engine"; description = "Backend achievement engine and concealed server-side rule evaluation." },
    @{ title = "Stage 10 - Native Achievement Unlock Experience"; description = "Audio, animation, haptics, push notifications, and unlock presentation." },
    @{ title = "Stage 11 - Recurring Quests and Mobile Notifications"; description = "Backend recurrence generation and platform-native reminder notifications." },
    @{ title = "Stage 12 - Mobile Dashboard and Analytics"; description = "Phone-friendly summaries, charts, cached states, and progress views." },
    @{ title = "Stage 13 - Evidence and Native Device Features"; description = "Camera, media library, document picking, uploads, sharing, and permissions." },
    @{ title = "Stage 14 - Mobile Security and Reliability"; description = "Transport security, deep-link validation, redaction, cache handling, and lifecycle reliability." },
    @{ title = "Stage 15 - Native Mobile Testing and Acceptance Audit"; description = "Android, iOS, physical-device, lifecycle, accessibility, and release testing." },
    @{ title = "Stage 16 - App Store and Play Store Release"; description = "Signed builds, store assets, privacy disclosures, beta tracks, monitoring, and release audit." }
)

$milestoneNumbers = @{}
foreach ($stage in $stages) {
    $payload = @{ title = $stage.title; description = $stage.description } | ConvertTo-Json -Compress
    $created = $payload | gh api "repos/$Repo/milestones" --method POST --input - | ConvertFrom-Json
    $milestoneNumbers[$stage.title] = $created.number
}

function New-Body {
    param(
        [string]$Objective,
        [string[]]$Scope,
        [string[]]$Acceptance,
        [string]$Dependencies,
        [string[]]$OutOfScope
    )

    $lines = @("Objective", $Objective, "", "Scope")
    for ($i = 0; $i -lt $Scope.Count; $i++) { $lines += "$($i + 1). $($Scope[$i])" }
    $lines += @("", "Acceptance Criteria")
    for ($i = 0; $i -lt $Acceptance.Count; $i++) { $lines += "$($i + 1). $($Acceptance[$i])" }
    $lines += @("", "Dependencies", $Dependencies, "", "Out of Scope")
    for ($i = 0; $i -lt $OutOfScope.Count; $i++) { $lines += "$($i + 1). $($OutOfScope[$i])" }
    return ($lines -join "`n")
}

$issues = @(
    @{
        stage = "Stage 1 - Product Rules and Domain Foundation"; title = "Define server-authoritative progression rules"; labels = @("documentation", "backend", "security")
        objective = "Document the domain rules that keep quest completion, XP, levels, streaks, achievements, recurrence, duplicate prevention, and persistence authoritative on the backend."
        scope = @("Define which calculations are backend-only.", "Document accepted mobile responsibilities.", "Document server timestamp usage.", "Document device clock manipulation handling.", "Document local versus server timestamp rules.")
        acceptance = @("The server timestamp is authoritative for progression calculations.", "The mobile device cannot independently manipulate XP or streaks.", "Backend-only progression responsibilities are documented.", "Mobile-only presentation and queueing responsibilities are documented.", "The rule document is linked from the repository README or docs index.")
        dependencies = "None."
        out = @("Implementing backend progression code.", "Implementing mobile screens.", "Store submission.")
    },
    @{
        stage = "Stage 1 - Product Rules and Domain Foundation"; title = "Document offline, conflict, and multi-device behavior"; labels = @("documentation", "synchronization", "mobile")
        objective = "Define mobile-specific product behavior for offline completions, synchronization conflicts, notification denial, multiple devices, achievement presentation after reconnection, and app-closed unlocks."
        scope = @("Document offline quest completion policy.", "Define conflict-resolution behavior.", "Define duplicate offline submission handling.", "Define multiple-device synchronization rules.", "Document notification permission denial behavior.", "Document achievement unlock presentation after reconnection or app restart.")
        acceptance = @("Duplicate offline submissions cannot create duplicate completions.", "Conflict-resolution behavior is documented.", "Notification permission is optional.", "Denying notifications does not prevent normal application use.", "Multiple devices can synchronize without duplicating rewards.", "Achievement unlocks received while closed have a documented presentation path.")
        dependencies = "Define server-authoritative progression rules."
        out = @("Building the offline queue.", "Building push notifications.", "Implementing the achievement rules engine.")
    },
    @{
        stage = "Stage 2 - Mobile and Backend Application Foundation"; title = "Create the React Native Expo application foundation"; labels = @("frontend", "mobile", "infrastructure")
        objective = "Create the installable mobile application foundation using React Native, TypeScript, Expo, and Expo Router."
        scope = @("Create the React Native and Expo application.", "Configure TypeScript.", "Configure Expo Router.", "Configure Android application identifiers.", "Configure iOS bundle identifiers.", "Configure environment-specific app configuration.", "Configure mobile API environments.", "Add mobile error boundaries.")
        acceptance = @("The application starts on an Android emulator.", "The application starts on a physical Android device.", "The application can produce an Android development build.", "The application configuration supports an iOS development build.", "Navigation works without a browser.", "Development and production API URLs are configurable.", "Secrets are not embedded in the mobile bundle.", "Backend unavailability does not crash the application.")
        dependencies = "Define server-authoritative progression rules."
        out = @("Web frontend.", "Browser support.", "Production store submission.", "Offline synchronization.")
    },
    @{
        stage = "Stage 2 - Mobile and Backend Application Foundation"; title = "Create the FastAPI backend and worker foundation"; labels = @("backend", "database", "worker", "infrastructure")
        objective = "Create the backend services and local development environment required by the native mobile application."
        scope = @("Create the FastAPI backend.", "Configure PostgreSQL.", "Configure Redis.", "Configure Celery worker and scheduler.", "Configure database migrations.", "Configure environment variables.", "Create API health and readiness endpoints.", "Add structured backend logging.")
        acceptance = @("The mobile application can reach the backend API.", "PostgreSQL accepts backend connections.", "Redis accepts backend and worker connections.", "The worker starts successfully.", "The scheduler starts successfully.", "Database migrations apply successfully.", "Health and readiness endpoints report required dependency status.", "Structured logs exclude secrets.")
        dependencies = "Create the React Native Expo application foundation."
        out = @("Achievement features.", "Recurring quest generation logic.", "Production deployment.")
    },
    @{
        stage = "Stage 3 - Database Schema and Data Integrity"; title = "Create core product schema and migrations"; labels = @("backend", "database", "testing")
        objective = "Define the PostgreSQL schema for users, campaigns, quests, completions, XP ledger entries, levels, streaks, achievements, and achievement progress."
        scope = @("Create SQLAlchemy models.", "Create Alembic migrations.", "Define uniqueness constraints for completions and rewards.", "Define ownership constraints.", "Add seed or fixture strategy where useful.", "Add migration verification tests.")
        acceptance = @("Migrations apply successfully from a clean database.", "Core records are associated with the correct user.", "Duplicate reward-producing records are rejected where required.", "Ownership constraints prevent cross-user data access.", "Migration rollback limitations are documented.")
        dependencies = "Create the FastAPI backend and worker foundation."
        out = @("Mobile UI.", "Achievement evaluation logic.", "Production migrations.")
    },
    @{
        stage = "Stage 3 - Database Schema and Data Integrity"; title = "Add device, push-token, and synchronization tables"; labels = @("database", "security", "synchronization", "notifications")
        objective = "Add data structures for registered devices, push tokens, synchronization operations, client mutations, device sessions, and notification delivery auditing."
        scope = @("Add RegisteredDevice.", "Add PushToken.", "Add SynchronizationOperation.", "Add ClientMutation.", "Add DeviceSession.", "Add NotificationDelivery.", "Add constraints for user ownership and idempotency.")
        acceptance = @("Push tokens are associated with the correct user and device.", "Invalidated push tokens can be deactivated.", "Duplicate client mutation identifiers are rejected.", "A synchronization operation cannot affect another user's records.", "Device removal invalidates the associated session where required.", "Notification delivery attempts are auditable.")
        dependencies = "Create core product schema and migrations."
        out = @("Push delivery service integration.", "Mobile token registration UI.", "Achievement presentation.")
    },
    @{
        stage = "Stage 4 - Mobile Authentication and Device Security"; title = "Implement mobile authentication flows"; labels = @("frontend", "backend", "security", "mobile")
        objective = "Implement registration, sign-in, sign-out, session refresh, protected routes, expired-session handling, and account deactivation for the native application."
        scope = @("Register users.", "Sign users in.", "Sign users out.", "Refresh authenticated sessions.", "Protect authenticated routes.", "Handle expired sessions.", "Revoke device sessions.", "Support account deactivation.", "Handle token refresh failure.")
        acceptance = @("A valid user can register.", "A valid user can sign in.", "Invalid credentials produce a controlled error.", "Signing out removes or invalidates local authentication data.", "Protected screens cannot be opened without a valid session.", "Expired sessions trigger a controlled reauthentication flow.", "Device sessions can be invalidated from the backend.", "Offline launch follows documented session behavior.")
        dependencies = "Add device, push-token, and synchronization tables."
        out = @("Browser cookies.", "Enterprise single sign-on.", "Passwordless authentication in the initial release.")
    },
    @{
        stage = "Stage 4 - Mobile Authentication and Device Security"; title = "Store credentials securely on device"; labels = @("frontend", "security", "mobile")
        objective = "Use platform-supported secure storage for supported authentication data and remove protected local data during logout or account switching."
        scope = @("Store supported credentials securely.", "Use Expo SecureStore or equivalent platform secure storage.", "Prevent sensitive values from appearing in logs.", "Clear protected local data after logout.", "Add optional biometric re-entry after initial authentication.", "Handle authentication while offline.")
        acceptance = @("Authentication secrets are not stored in ordinary unencrypted application storage.", "Secure local values use the platform-supported secure-storage mechanism.", "Biometric access does not replace backend authentication.", "Sensitive authentication data is excluded from logs.", "Another user cannot recover the previous user's cached private data.", "Logout clears protected cached data.")
        dependencies = "Implement mobile authentication flows."
        out = @("Mandatory biometrics.", "Passwordless authentication.", "Enterprise device management.")
    },
    @{
        stage = "Stage 5 - Native Mobile Design System and Navigation"; title = "Create native navigation structure"; labels = @("frontend", "mobile", "testing")
        objective = "Create bottom-tab, stack, and modal navigation for Home, Campaigns, Quests, Achievements, and Profile."
        scope = @("Create bottom-tab navigation.", "Create stack navigation.", "Create modal navigation.", "Add safe-area handling.", "Add keyboard avoidance.", "Add Android back-button handling.", "Persist supported navigation state across lifecycle transitions.")
        acceptance = @("Navigation works on Android and iOS builds.", "Android system-back behavior is predictable.", "Screens respect safe areas.", "Forms remain usable when the software keyboard is visible.", "Navigation state survives supported application lifecycle transitions.", "No workflow depends on hover behavior.", "No screen requires a desktop viewport.")
        dependencies = "Create the React Native Expo application foundation."
        out = @("Web navigation.", "Sidebars.", "Desktop breakpoints.", "Browser keyboard shortcuts.")
    },
    @{
        stage = "Stage 5 - Native Mobile Design System and Navigation"; title = "Create accessible mobile design system components"; labels = @("frontend", "mobile", "documentation", "testing")
        objective = "Create reusable accessible mobile components, themes, state surfaces, and interaction standards for the native application."
        scope = @("Add light and dark themes.", "Add native form controls.", "Add buttons and touch states.", "Add cards and list items.", "Add bottom sheets where appropriate.", "Add loading skeletons.", "Add empty, error, offline, and synchronization states.", "Add accessible labels, roles, scalable typography, reduced-motion support, and touch-target standards.")
        acceptance = @("Primary touch targets are sufficiently large and separated.", "Screen-reader labels identify interactive controls.", "Application text responds appropriately to supported system font scaling.", "Status is not communicated through color alone.", "Reduced-motion preferences disable nonessential animation.", "Light and dark themes remain readable.", "Loading, empty, error, and offline states are distinguishable.", "Screen-reader testing requirements are documented.")
        dependencies = "Create native navigation structure."
        out = @("Mouse-specific interaction.", "Desktop-only layouts.", "Production visual polish for every future feature.")
    },
    @{
        stage = "Stage 6 - Campaign and Quest Management"; title = "Build native campaign management"; labels = @("frontend", "backend", "mobile")
        objective = "Implement mobile-first campaign creation, listing, editing, filtering, and deletion flows."
        scope = @("Create native campaign lists.", "Create campaign create and edit forms.", "Use bottom-sheet or modal creation flows where appropriate.", "Add pull-to-refresh.", "Add touch-friendly filtering.", "Add native confirmation prompts.", "Protect unsaved form changes from accidental dismissal.")
        acceptance = @("Campaigns can be created using the on-screen keyboard.", "Creation forms remain visible while the keyboard is open.", "Pull-to-refresh synchronizes server data.", "Unsaved form changes are protected from accidental dismissal.", "Lists remain usable with representative portfolio data volumes.", "Campaign actions have accessible alternatives.")
        dependencies = "Create accessible mobile design system components."
        out = @("Desktop campaign interface.", "Advanced analytics.", "Fully offline campaign editing.")
    },
    @{
        stage = "Stage 6 - Campaign and Quest Management"; title = "Build native quest management"; labels = @("frontend", "backend", "mobile")
        objective = "Implement mobile-first quest creation, listing, editing, filtering, recurrence selection, and deletion flows."
        scope = @("Create native quest lists.", "Use mobile date and time pickers.", "Add swipe actions only when accessible alternatives exist.", "Add pull-to-refresh.", "Add touch-friendly filtering.", "Add native confirmation prompts.", "Support quest association with campaigns.")
        acceptance = @("Quests can be created using the on-screen keyboard.", "Creation forms remain visible while the keyboard is open.", "Pull-to-refresh synchronizes server data.", "Swipe actions have visible non-swipe alternatives.", "Date selectors behave correctly on Android and iOS.", "Unsaved form changes are protected from accidental dismissal.", "Lists remain usable with representative portfolio data volumes.")
        dependencies = "Build native campaign management."
        out = @("Recurring quest backend generation.", "Quest completion synchronization.", "Desktop quest UI.")
    },
    @{
        stage = "Stage 7 - Quest Completion and Synchronization"; title = "Implement online quest completion"; labels = @("frontend", "backend", "synchronization", "mobile")
        objective = "Support reliable quest completion while online while preserving backend authority and preventing duplicate submissions."
        scope = @("Complete quests while online.", "Optimistically update supported interface states.", "Roll back invalid optimistic changes.", "Prevent duplicate submissions.", "Preserve server authority.", "Display synchronized state.", "Support completions made on another device after refresh or synchronization.")
        acceptance = @("Online completion is persisted by the backend.", "Rapid repeated taps do not create duplicate completions.", "Server rejection restores the correct interface state.", "A completion made on another device appears after synchronization.", "Device time does not determine authoritative XP or streak results.", "Pending, synchronized, and failed states are visually distinguishable.")
        dependencies = "Build native quest management."
        out = @("Fully offline account creation.", "Peer-to-peer synchronization.", "Device-authoritative progression.")
    },
    @{
        stage = "Stage 7 - Quest Completion and Synchronization"; title = "Implement offline completion queue and replay"; labels = @("frontend", "backend", "database", "synchronization", "security")
        objective = "Queue supported quest completions while offline and synchronize them safely after reconnection."
        scope = @("Queue supported completions while offline.", "Assign unique client mutation identifiers.", "Synchronize queued completions.", "Handle synchronization conflicts.", "Retry recoverable failures.", "Stop retrying permanent failures.", "Provide a manual retry action.", "Safely handle or remove queued private operations on logout.")
        acceptance = @("Offline completion creates a clearly identified pending operation.", "Pending operations survive supported application restarts.", "Reconnection attempts synchronization.", "Replayed operations cannot award duplicate XP.", "Permanent validation failures are shown to the user.", "Recoverable failures can be retried.", "Logging out safely handles or removes queued private operations.", "Duplicate client mutation identifiers are rejected by the backend.")
        dependencies = "Implement online quest completion."
        out = @("Unlimited offline history.", "Editing all data types while offline.", "Peer-to-peer synchronization.")
    },
    @{
        stage = "Stage 8 - XP, Levels and Streaks"; title = "Implement server-authoritative XP, levels, and streaks"; labels = @("backend", "database", "testing")
        objective = "Implement backend progression calculations for XP awards, level calculations, streak updates, and append-only progress history."
        scope = @("Award XP on validated completions.", "Calculate levels on the backend.", "Calculate streaks on the backend.", "Persist authoritative progression records.", "Prevent duplicate XP awards.", "Expose synchronized totals through the API.", "Add tests for duplicate and timezone-sensitive cases.")
        acceptance = @("XP displayed by the device matches the server ledger after synchronization.", "Streak values remain server-authoritative.", "Device clock changes cannot independently manipulate XP or streaks.", "Duplicate completion replay cannot award duplicate XP.", "Level calculations are repeatable from authoritative data.", "Tests cover primary progression paths.")
        dependencies = "Implement offline completion queue and replay."
        out = @("Mobile XP animation.", "Achievement evaluation.", "Manual admin reward adjustment.")
    },
    @{
        stage = "Stage 8 - XP, Levels and Streaks"; title = "Present XP, levels, and streaks in the mobile app"; labels = @("frontend", "mobile", "synchronization")
        objective = "Display synchronized XP gain, level progress, streak indicators, haptic feedback, and offline pending states in the native application."
        scope = @("Add XP gain animation.", "Add level-progress bar.", "Add streak indicator.", "Trigger configurable haptic feedback.", "Display synchronized totals.", "Display offline pending state.", "Avoid repeated level-up events after restart.")
        acceptance = @("XP animation does not run before server confirmation unless explicitly presented as pending.", "Haptic feedback can be disabled where appropriate.", "Level-up events are not presented repeatedly after application restart.", "Offline pending state is distinct from confirmed progression.", "Displayed totals match the backend after synchronization.")
        dependencies = "Implement server-authoritative XP, levels, and streaks."
        out = @("Achievement unlock presentation.", "Push notifications.", "Desktop dashboard charts.")
    },
    @{
        stage = "Stage 9 - Achievement Rules Engine"; title = "Build the backend achievement rules engine"; labels = @("backend", "database", "security", "testing")
        objective = "Implement the server-side achievement engine as the primary backend differentiator without trusting editable client state."
        scope = @("Define achievement definitions and versions.", "Evaluate threshold conditions.", "Evaluate streak conditions.", "Evaluate category conditions.", "Evaluate campaign conditions.", "Evaluate date-window conditions.", "Persist progress and unlocks.", "Prevent duplicate achievement unlocks.")
        acceptance = @("The mobile application cannot directly award an achievement.", "Achievement evaluation runs on authoritative backend records.", "Rules and internal evaluation details are not trusted from editable client state.", "Hidden achievement conditions remain concealed.", "Duplicate evaluation does not create duplicate unlocks.", "Offline completion can trigger an achievement only after server synchronization.", "Tests cover major rule types.")
        dependencies = "Implement server-authoritative XP, levels, and streaks."
        out = @("Native achievement unlock animation.", "Steam assets or branding.", "Client-side rule execution.")
    },
    @{
        stage = "Stage 9 - Achievement Rules Engine"; title = "Render achievement progress in the mobile app"; labels = @("frontend", "mobile", "security")
        objective = "Display achievement collections and progress received from the server while preserving hidden-condition behavior."
        scope = @("Render unlocked achievements.", "Render visible locked achievements.", "Render server-provided progress.", "Conceal hidden achievement conditions.", "Display sync-pending achievement state where appropriate.", "Handle refresh after offline synchronization.")
        acceptance = @("Achievement progress received from the server is rendered correctly.", "Hidden achievement conditions remain concealed.", "The app cannot edit achievement progress locally to award achievements.", "Offline completion does not present a confirmed unlock before server synchronization.", "Achievement collection remains usable on supported phone sizes.")
        dependencies = "Build the backend achievement rules engine."
        out = @("Push notifications.", "Unlock audio and haptics.", "Custom user-uploaded sounds.")
    },
    @{
        stage = "Stage 10 - Native Achievement Unlock Experience"; title = "Implement foreground achievement unlock presentation"; labels = @("frontend", "mobile", "notifications")
        objective = "Create a distinctive accessible in-app achievement unlock experience using native audio, animation, and haptic feedback."
        scope = @("Receive achievement-unlock events while the app is open.", "Display an in-app achievement banner.", "Display a full achievement-unlock presentation.", "Play an original achievement sound.", "Trigger configurable haptic feedback.", "Respect device silent behavior where required.", "Respect app sound settings.", "Respect reduced-motion settings.", "Prevent duplicate presentations.", "Provide an accessible non-audio equivalent.")
        acceptance = @("An achievement unlock is first persisted by the backend.", "A foregrounded application receives the unlock.", "An original or properly licensed sound is used.", "Sound can be disabled.", "Haptic feedback can be disabled where supported.", "Reduced-motion mode presents an accessible alternative.", "The unlock remains understandable without sound.", "The unlock remains understandable without animation.", "A previously acknowledged unlock is not repeatedly presented.")
        dependencies = "Render achievement progress in the mobile app."
        out = @("Steam sound assets.", "Steam iconography.", "Steam branding.", "Custom user-uploaded sounds.", "Critical-alert permissions.")
    },
    @{
        stage = "Stage 10 - Native Achievement Unlock Experience"; title = "Implement achievement push notifications and history"; labels = @("frontend", "backend", "notifications", "mobile")
        objective = "Deliver and handle achievement push notifications while the app is backgrounded or closed, including deep links and unread history."
        scope = @("Receive push notifications while backgrounded or closed.", "Store unread unlock notifications.", "Deep-link notifications to achievement details.", "Handle unlocks received on multiple devices.", "Handle notification permission denial.", "Prevent duplicate push presentations.")
        acceptance = @("A backgrounded application can receive a push notification when platform delivery succeeds.", "Tapping a notification opens the correct achievement.", "Duplicate push delivery does not create duplicate achievements.", "Notification denial does not block achievement access inside the application.", "Missed unlocks remain available in notification history.", "The experience works on both Android and iOS builds.")
        dependencies = "Implement foreground achievement unlock presentation."
        out = @("Promotional notification spam.", "Critical-alert permissions.", "SMS or email notifications.")
    },
    @{
        stage = "Stage 11 - Recurring Quests and Mobile Notifications"; title = "Generate recurring quests and reminders on the backend"; labels = @("backend", "worker", "database", "notifications")
        objective = "Generate recurring quest occurrences and reminder events on the backend without depending on mobile background execution."
        scope = @("Generate recurring quest occurrences on the backend.", "Schedule reminder events on the backend.", "Handle changed recurrence schedules.", "Handle timezone changes.", "Prevent duplicate reminders.", "Prevent duplicate occurrences.", "Retain authoritative historical timestamps.")
        acceptance = @("Recurring occurrences are generated without the application being open.", "Closing the mobile application does not stop backend recurrence processing.", "Exact progression logic does not depend on mobile background execution.", "Duplicate scheduler execution does not produce duplicate occurrences.", "Timezone changes update future reminder behavior.", "Historical completions retain their original authoritative timestamps.")
        dependencies = "Build native quest management."
        out = @("Dependence on continuously running mobile background timers.", "Alarm-clock functionality.", "Location-triggered reminders.")
    },
    @{
        stage = "Stage 11 - Recurring Quests and Mobile Notifications"; title = "Register devices and send quest reminder notifications"; labels = @("frontend", "backend", "notifications", "mobile", "security")
        objective = "Register mobile push tokens, send reminder notifications, manage permission state, and open the relevant quest from a notification."
        scope = @("Register device push tokens.", "Send remote push notifications.", "Schedule appropriate local notifications.", "Cancel outdated local notifications.", "Handle notification permission state.", "Open the relevant quest from a notification.", "Deactivate invalid push tokens.", "Display notification settings.")
        acceptance = @("A valid device can register for notifications.", "Permission is requested in context rather than immediately without explanation.", "A reminder opens the related quest.", "Invalid device tokens are handled.", "Disabled notification categories are respected.", "Users without notification permission can still view upcoming quests in the application.")
        dependencies = "Generate recurring quests and reminders on the backend."
        out = @("SMS reminders.", "Email reminders.", "Location-triggered reminders.", "Promotional notification spam.")
    },
    @{
        stage = "Stage 12 - Mobile Dashboard and Analytics"; title = "Create the mobile dashboard"; labels = @("frontend", "mobile", "synchronization")
        objective = "Create phone-friendly dashboard summaries for progress, quests, campaigns, achievements, streaks, and cached synchronization states."
        scope = @("Add mobile summary cards.", "Add campaign progress rings or bars.", "Add achievement collection grids.", "Add streak calendars.", "Add weekly summaries.", "Add pull-to-refresh.", "Represent cached data when offline.")
        acceptance = @("Analytics are readable on supported phone sizes.", "The dashboard does not depend on horizontal desktop layouts.", "Pull-to-refresh updates the dashboard.", "Cached data is clearly distinguished when synchronization is unavailable.", "Long lists use appropriate mobile rendering and pagination strategies.")
        dependencies = "Present XP, levels, and streaks in the mobile app."
        out = @("Desktop charts.", "Dense data tables.", "Hover-dependent inspection.")
    },
    @{
        stage = "Stage 12 - Mobile Dashboard and Analytics"; title = "Create touch-accessible mobile analytics"; labels = @("frontend", "mobile", "testing")
        objective = "Create mobile analytics views with touch-accessible filters, scrollable charts, and accessible alternatives."
        scope = @("Add swipeable or vertically stacked analytics.", "Add touch-accessible date filters.", "Add scrollable charts.", "Add reduced-data summaries for small displays.", "Add accessible alternatives for chart values.", "Test representative phone sizes.")
        acceptance = @("Charts do not require hover interaction.", "Chart values can be inspected using touch and accessible alternatives.", "Analytics remain readable on supported phone sizes.", "Small displays receive reduced-data summaries where needed.", "Tests cover key chart and filter states.")
        dependencies = "Create the mobile dashboard."
        out = @("Desktop analytics tables.", "Advanced BI exports.", "Admin-only analytics.")
    },
    @{
        stage = "Stage 13 - Evidence and Native Device Features"; title = "Implement evidence capture and upload"; labels = @("frontend", "backend", "mobile", "security")
        objective = "Allow users to capture or select evidence, upload it securely, and handle native permissions safely."
        scope = @("Capture evidence using the device camera.", "Select evidence from the photo library.", "Select supported documents.", "Compress images where appropriate.", "Upload evidence securely.", "Display upload progress.", "Retry failed uploads.", "Remove local temporary files.", "Control evidence privacy.", "Request device permissions only when required.")
        acceptance = @("Camera access is requested only when the user selects camera capture.", "Media-library access is requested only when required.", "Denying permission does not crash the application.", "The user receives an alternative when a permission is denied.", "Unsupported files are rejected.", "Oversized files are rejected or safely compressed according to documented rules.", "Upload progress is visible.", "Failed uploads can be retried.", "Private evidence cannot be accessed publicly.", "Temporary sensitive files are not retained unnecessarily.")
        dependencies = "Build native quest management."
        out = @("Public evidence galleries.", "Unrestricted file uploads.", "Background bulk media backup.")
    },
    @{
        stage = "Stage 13 - Evidence and Native Device Features"; title = "Generate and share achievement images"; labels = @("frontend", "mobile", "security")
        objective = "Generate approved achievement share images and open the native share sheet."
        scope = @("Generate shareable achievement images.", "Open the native share sheet.", "Use only approved achievement and user information.", "Avoid exposing private evidence.", "Handle share cancellation and failure states.")
        acceptance = @("Shared achievement images use only approved information.", "Native sharing works on supported Android and iOS devices.", "Private evidence cannot be included without explicit product approval.", "Share cancellation does not create an error state.", "Generated files are cleaned up when no longer needed.")
        dependencies = "Render achievement progress in the mobile app."
        out = @("Custom user-designed templates.", "Social-network API posting.", "Steam branding.")
    },
    @{
        stage = "Stage 14 - Mobile Security and Reliability"; title = "Harden mobile security boundaries"; labels = @("security", "frontend", "backend", "mobile")
        objective = "Review and harden transport security, local data handling, deep links, notification content, logging, and compromised-device limitations."
        scope = @("Configure certificate and transport security.", "Review sensitive screenshots.", "Review clipboard data handling.", "Validate deep links.", "Protect notification-content privacy.", "Document rooted or compromised-device limitations.", "Redact logs.", "Protect local database contents.", "Invalidate push tokens.")
        acceptance = @("Private values do not appear in notification previews unless explicitly appropriate.", "Deep links validate authentication and resource ownership.", "Sensitive tokens do not appear in logs.", "Local databases do not store unnecessary secrets.", "Invalid deep links fail safely.", "The application uses encrypted HTTPS communication in production.", "Production configuration excludes development API endpoints.", "Rooted or compromised-device limitations are documented.")
        dependencies = "Store credentials securely on device."
        out = @("Formal penetration test.", "Device attestation enforcement.", "Enterprise mobile device management.")
    },
    @{
        stage = "Stage 14 - Mobile Security and Reliability"; title = "Test lifecycle and synchronization reliability"; labels = @("testing", "synchronization", "mobile", "security")
        objective = "Verify logout, reinstall, account switching, network interruption, cache removal, API rate limits, offline queue integrity, and lifecycle transitions."
        scope = @("Test cache removal after logout.", "Document reinstall behavior.", "Document account-switching behavior.", "Test network interruption during synchronization.", "Verify API rate limiting behavior.", "Verify offline queue integrity.", "Test application lifecycle transitions.")
        acceptance = @("Logout clears protected cached data.", "Reinstall and account-switching behavior is documented.", "Network interruption does not corrupt local synchronization state.", "API rate limits produce controlled user-facing behavior.", "Offline queue integrity is preserved across expected lifecycle transitions.", "Application lifecycle testing results are recorded.")
        dependencies = "Implement offline completion queue and replay."
        out = @("Long-term soak testing.", "Multi-region failure testing.", "Production incident response process.")
    },
    @{
        stage = "Stage 15 - Native Mobile Testing and Acceptance Audit"; title = "Create automated mobile and backend test coverage"; labels = @("testing", "frontend", "backend", "mobile")
        objective = "Add automated tests for domain logic, mobile presentation logic, API communication, navigation, offline synchronization, permissions, sessions, and app upgrades."
        scope = @("Unit-test domain and mobile presentation logic.", "Integration-test API communication.", "Test Android navigation.", "Test iOS navigation.", "Test offline and reconnection flows.", "Test permission denial.", "Test session expiration.", "Test app-version upgrades.", "Test representative low-performance devices where automation allows.")
        acceptance = @("Critical workflows have automated coverage where practical.", "Offline synchronization does not duplicate progress.", "Notification denial is handled.", "Camera and media permission denial are handled.", "Session expiration produces a controlled result.", "The application recovers from backend unavailability.", "No criterion is marked passed without evidence.")
        dependencies = "Complete the primary MVP functional flow."
        out = @("Full manual release audit.", "Store submission.", "External QA vendor process.")
    },
    @{
        stage = "Stage 15 - Native Mobile Testing and Acceptance Audit"; title = "Run physical-device acceptance audit"; labels = @("testing", "mobile", "notifications", "release")
        objective = "Verify the MVP on real Android and iOS devices under realistic lifecycle, accessibility, notification, audio, haptic, and performance conditions."
        scope = @("Test physical Android devices.", "Test physical iOS devices.", "Test application backgrounding.", "Test application termination and reopening.", "Test push notifications.", "Test deep links.", "Test audio and haptics.", "Test reduced motion.", "Test large font sizes.", "Test screen readers.", "Test keyboard interaction.", "Record evidence for each acceptance item.")
        acceptance = @("Critical workflows pass on Android.", "Critical workflows pass on iOS.", "At least one physical device from each supported platform is tested.", "Quest completion survives expected lifecycle transitions.", "Push notification deep links work.", "Achievement audio can be disabled.", "Achievement haptics can be disabled where supported.", "Reduced-motion behavior is verified.", "Large-text layouts remain usable.", "Screen-reader navigation is verified.", "No criterion is marked passed without evidence.")
        dependencies = "Create automated mobile and backend test coverage."
        out = @("App Store submission.", "Play Store submission.", "Formal accessibility certification.")
    },
    @{
        stage = "Stage 16 - App Store and Play Store Release"; title = "Produce signed Android and iOS release builds"; labels = @("release", "infrastructure", "mobile", "security")
        objective = "Configure production identifiers, signing, icons, splash screens, testing tracks, and signed release artifacts for Android and iOS."
        scope = @("Configure production application identifiers.", "Configure Android signing.", "Configure iOS signing.", "Create production builds.", "Create application icons.", "Create splash screens.", "Configure internal testing.", "Configure iOS beta testing.", "Configure Android testing tracks.", "Submit release candidates.")
        acceptance = @("A signed Android App Bundle is generated.", "A signed iOS application archive is generated.", "The Android application installs through a testing track.", "The iOS application installs through the selected beta-distribution process.", "Application identifiers match production configuration.", "No development credentials are included.", "No unfinished controls appear operational.")
        dependencies = "Run physical-device acceptance audit."
        out = @("Web deployment.", "Tablet-specific redesign in the initial release.", "Apple Watch application.", "Wear OS application.", "Desktop application.")
    },
    @{
        stage = "Stage 16 - App Store and Play Store Release"; title = "Prepare store metadata, monitoring, and release audit"; labels = @("release", "documentation", "security", "notifications")
        objective = "Prepare store screenshots, descriptions, privacy disclosures, permission explanations, production monitoring, crash reporting, demo materials, limitations, and architecture diagrams."
        scope = @("Prepare store screenshots.", "Prepare store descriptions.", "Prepare privacy disclosures.", "Prepare permission explanations.", "Resolve store-review defects.", "Add production monitoring.", "Add crash reporting.", "Seed a demonstration account where appropriate.", "Record a mobile demonstration video.", "Document known limitations.", "Create architecture and synchronization diagrams.", "Review against current Apple and Google requirements before submission.")
        acceptance = @("Store screenshots represent the actual application.", "Privacy disclosures correspond to actual data processing.", "Permission descriptions correspond to implemented functionality.", "The application passes internal release verification.", "Production API endpoints use HTTPS.", "Crash reporting receives a controlled test event.", "Push notifications work with production credentials.", "Store metadata does not claim Steam affiliation.", "The application is reviewed against current Apple and Google requirements before submission.")
        dependencies = "Produce signed Android and iOS release builds."
        out = @("GitHub configuration.", "GitHub Actions.", "Tablet-specific redesign in the initial release.", "Desktop application.")
    }
)

foreach ($issue in $issues) {
    $body = New-Body -Objective $issue.objective -Scope $issue.scope -Acceptance $issue.acceptance -Dependencies $issue.dependencies -OutOfScope $issue.out
    $labelArg = ($issue.labels -join ",")
    gh issue create --repo $Repo --title $issue.title --body $body --label $labelArg --milestone $issue.stage | Out-Null
}

Write-Output "Created $($issues.Count) issues across $($stages.Count) stage milestones in $Repo."
