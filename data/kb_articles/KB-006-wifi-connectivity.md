# KB-006: Wi-Fi connectivity — symptom-based helpdesk triage

This is an original synthetic training article for the course project. It defines a fictional helpdesk workflow, not an organization's approved operating procedure or a copy of a Microsoft article. The workflow separates an unclear report from a confirmed symptom so that a previous incident is not mistaken for a diagnosis of the current device.

## Start with an observable Wi-Fi symptom

The statement "my Wi-Fi is not working" is incomplete. In this sample workflow, the first question distinguishes four observations: the network is missing, joining the network fails, the device joins but reports no internet, or the connection drops after initially working. One useful question is whether the device cannot connect at all or connects without internet access. A reply naming Windows 11 identifies an environment but still does not identify the failure.

The fictional analyst records the user's observation separately from an interpretation. "The laptop displays no available networks" is an observation; "the adapter is broken" is an unverified explanation. A reported symptom should not be rewritten as a confirmed hardware failure. A request for the exact displayed message is useful when the user has already confirmed that joining a visible network fails.

## Known network is absent from the available networks list

For a Windows device that cannot see a known Wi-Fi network, the low-impact checks in this training workflow are to confirm that Wi-Fi is enabled and airplane mode is off, then check whether a second device can see the same network. Record the results rather than treating either result as proof of a particular cause. Availability of a network and successful internet access are different observations.

This branch is for a missing network name. It does not justify changing VPN settings or treating a VPN error as a wireless adapter fault. In the fictional helpdesk record, the useful comparison is whether the same network is visible on a second device at the same location and time. There is no need to record the second device owner's name. A network missing only from the affected laptop and a network missing from all tested devices require different follow-up investigation.

## Connected to Wi-Fi but no internet access

If Windows shows a Wi-Fi connection with no internet, record that exact state. Check whether another device has internet access on the same network, and whether the affected laptop can open more than one approved public website. For a Windows 11 device, the Network and Internet troubleshooter in Get Help can be used where permitted. Capture its result without assuming that running it fixed the problem.

In this fictional workflow, the second-device check is a way to narrow the scope of investigation. If multiple devices are affected, collect the location, approximate start time and shared symptom for the helpdesk. If only the laptop is affected, retain that distinction in the record. Neither finding alone proves a router fault, a service-provider outage, a DNS problem or a damaged adapter. An isolated application failure should be described as such rather than automatically labeled a complete loss of connectivity.

## Intermittent drops and changes of location

For intermittent Wi-Fi connectivity, the sample analyst asks when the drop occurs: while staying in one place, after moving rooms, or after changing between home Wi-Fi and a hotspot. A timeline helps separate loss of the wireless connection from loss of a VPN tunnel. Record what the network indicator and the VPN application each showed at the time. An estimated time is acceptable if the user does not know the exact minute.

The synthetic incident dataset separately documents VPN disconnections during a network handoff. That historical resolution does not establish the cause of every wireless drop. If Wi-Fi remains connected but the VPN disconnects, use the VPN branch after confirming the observation. If both disconnect, document their order and request the next missing observation. The sample workflow avoids silently converting "my VPN stopped" into "my wireless network disappeared."

## An error appears in a different application

An error code belongs to the application or connection attempt that displayed it. If a user describes Wi-Fi trouble and later reports error 789, the sample analyst first asks whether that code appeared when joining Wi-Fi or when starting the VPN. The label "Wi-Fi problem" from an earlier message does not settle that question. A numeric code without its display context is not enough to recommend a configuration change.

For this training workflow, the useful evidence is the application name, the exact message and the action immediately preceding it. Screenshots should omit personal messages, secrets and unrelated account information. If the user cannot identify the application, ask for one visible detail rather than presenting a long technical checklist. The incident remains unclear until the relevant action is established.

## Scope of assistance and helpdesk handoff

This sample employee-facing workflow ends before administrator commands, adapter removal, network reset, certificate changes or changes to shared network equipment. Those actions require an approved organizational process and assessment by the responsible team. A request to perform privileged or security-sensitive changes is a human-escalation case, not permission to generate instructions from a loosely related incident.

A useful handoff contains the confirmed symptom, affected device type, approximate start time, whether another device was affected, and the checks already performed with their results. Unknown values remain unknown. A report that a colleague also had trouble is a user observation, not an independently verified outage. The sample assistant cannot submit the report or claim that a helpdesk ticket exists.

## Background reference

Microsoft's public Wi-Fi troubleshooting page provides background for the short Windows checks above. The fictional triage examples and handoff conventions are original course content. Always use the organization's current procedures for managed devices.

https://support.microsoft.com/en-us/windows/experience/connectivity-networking/fix-wi-fi-connection-issues-in-windows
