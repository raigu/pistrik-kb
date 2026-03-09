# PISTRIK Regulatory Context

> **Last researched**: 2026-03-06
>
> Point-in-time snapshot. Re-research periodically as the system is under active development.
> Sources listed at the bottom.

## What is PISTRIK

PISTRIK is Estonia's new waste information system (jäätmeinfosüsteem), a subsystem of KOTKAS. It replaces two legacy systems:

- **OJS** — hazardous waste transport document register
- **KOTKAS waste reporting module** — annual waste reports

PISTRIK combines waste transport waybills (saatekirjad) and waste reporting into a single system where one document serves both purposes: documenting physical waste movement AND updating both companies' waste balances.

## Three-Party Transaction Model

Each waste transaction connects three parties:

| Party | Role |
|-------|------|
| Waste generator (jäätmetekitaja) | Creates the waybill before transport |
| Carrier (vedaja) | Transports waste |
| Processor (käitleja) | Receives and processes waste |

## Legislative Basis

- **Waste Act amendment (eelnõu 657 SE)** — passed by Riigikogu, signed by President on Dec 23, 2025
- **Enters force**: January 1, 2026
- Amends 6 laws: Waste Act, Environmental Code General Part Act, District Heating Act, Environmental Fees Act, Local Government Organization Act, Packaging Act
- Part of the broader **jäätmereform** (waste reform) led by Ministry of Climate

## Timeline

| Date | Milestone |
|------|-----------|
| Jan 1, 2026 | Waste Act amendment enters force |
| 2026 | ~12 municipalities run new waste tenders |
| 2027 | PISTRIK full deployment target |
| 2030 | New system in effect in all municipalities |

## Reporting Requirements

- **Waybills** must be created and submitted before waste transport begins
- **Quarterly reports** due by the 8th of the following quarter (replaces annual Jan 31 deadline)
- Annual summary reports are auto-generated from waybill data and quarterly reports

## Integration Options

| Channel | Description |
|---------|-------------|
| Self-service portal | Web UI at pistrikkoolitus.envir.ee (test environment) |
| API (M2M) | Machine-to-machine data exchange interface |
| X-Road | First subsystem published in TEST environment |

### API Resources

- **OpenAPI spec**: https://pistrikkoolitus.envir.ee/docs
- **GitHub wiki**: https://github.com/kemitgituser/pistrik-api-documentation/wiki
- **Postman collection**: https://www.postman.com/pistrik/pistrik-public/overview

## Funding

- Environmental Investment Centre offers financial support for companies developing API integrations
- State allocates EUR 35M for municipal collection infrastructure
- EUR 14M for recycling capacity development

## Support Contacts

| Contact | Details |
|---------|---------|
| Client support | klienditugi@keskkonnaamet.ee, +372 662 5999 (weekdays 9-17) |
| System issues | pistrik@envir.ee |
| Environmental reporting advisor | Krisela Uussaar, krisela.uussaar@envir.ee, +372 5422 0353 |

## Sources

- [Jäätmeinfosüsteem PISTRIK — Keskkonnaportaal](https://keskkonnaportaal.ee/et/jaatmeinfosusteem-pistrik)
- [Jäätmevaldkond — Keskkonnaportaal](https://keskkonnaportaal.ee/et/teemad/reaalajamajandus/jaatmevaldkond)
- [Waste — Keskkonnaportaal (EN)](https://keskkonnaportaal.ee/en/topics/waste)
- [Jäätmereform — Kliimaministeerium](https://kliimaministeerium.ee/jaatmereform)
- [Waste Act amendment bill — Riigikogu](https://www.riigikogu.ee/pressiteated/keskkonnakomisjon-et-et/keskkonnakomisjon-saatis-jaatmeseaduse-muutmise-eelnou-esimesele-lugemisele-2/)
- [Estonia digital waste management — e-Estonia](https://e-estonia.com/estonia-planning-a-country-wide-digital-system-to-monitor-waste-management/)
