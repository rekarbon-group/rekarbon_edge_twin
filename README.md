# REKARBON — Edge-Native MRV Digital Twin

**Cryptographic carbon credit certification at sensor level.**

## What this is
A Streamlit simulation of REKARBON's edge MRV infrastructure — 
demonstrating real-time IoT data ingestion, Ed25519 hash-chain 
integrity, and Digital Twin certification for environmental credits.

## Stack
- Python / Streamlit
- Edge simulation (Raspberry Pi 5 architecture)
- Ed25519 cryptographic signing
- Digital Twin data pipeline

## Context
REKARBON addresses the 96% CDR delivery gap (46M tonnes committed, 
<1M delivered since 2019). This demo simulates the sensor-to-credit 
pipeline that generates GHG Protocol Land Sector Removals v1.0 
compliant instruments at €200+/tonne.

## Architecture
Sensors → Edge Node (PI#A) → Validator (PI#B) → Digital Twin → 
Registry-ready certified credit

## Links
- [rekarbon.com](https://rekarbon.com)
