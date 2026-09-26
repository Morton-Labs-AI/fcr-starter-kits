# Fusion Control Room starter kits

Learn how a reactor model becomes an inspectable, reproducible result. These
three small projects are the downloadable companion to Morton Labs' Fusion
Control Room. Start with prepared data, then inspect the code and assumptions.

| Kit | First run | What you reproduce |
| --- | --- | --- |
| [BEAVRS](beavrs/README.md) | Python 3.10+, no third-party packages | A published PWR benchmark's geometry and measurement projection |
| [Paramak](paramak/README.md) | Python 3.10+, no third-party packages | The recorded comparison of two checked geometry cases |
| [After fusion](after-fusion/README.md) | Node 22.12+ and a browser | Interactive playback of prepared plasma, transport, and heat results |

No account is required. Each kit is also available as an independent ZIP from
the portal. Run commands inside the corresponding kit directory. The beginner
paths do not require OpenMC, nuclear data, Docker, or a CAD installation.

Evidence is part of the interface: published measurements are observations;
checked geometry is geometry; prepared numerical results are a recorded model
run. None is a validated commercial reactor design. The two Paramak cases do
not establish a continuous design range. The After fusion plasma model is
independent of its neutron source; only transport deposition and thermal
response are quantitatively coupled.

Morton-authored code and adapters are available under **MIT OR Apache-2.0**, at
your option. Upstream BEAVRS and Paramak files retain their MIT notices and are
not relicensed. See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Review
[CONTRIBUTING.md](CONTRIBUTING.md) before sending a change.
