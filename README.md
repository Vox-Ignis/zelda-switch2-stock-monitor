# Zelda Switch 2 Stock Monitor

A Python stock-monitoring tool that checks multiple online retailers for availability of the Zelda 40th Anniversary Switch 2

Built as a personal Python and Playwright learning project.

## Features

- Monitors multiple retailers based on HTML elements
- Users Playwright for browser automation
- Detects multiple stock states:
    - IN STOCK
    - OUT OF STOCK
    - UNKNOWN
    - VERIFY
- Retailer-specific polling intervals
- Built-in cooldowns when verification pages
- Audible Windows alert
- Discord notification of IN STOCK availability
- Error handling for failed retailer checks

## Supported Retailers

- Best Buy
- GameStop
- Walmart
- Nintendo
- Amazon
- Target

## Requirements

- Python 3
- Playwright
- Chromium

## Installation

Clone repo:
  git clone https://github.com/Vox-Ignis/zelda-switch2-stock-monitor.git
  cd zelda-switch2-stock-monitor

Create virtual environment:
  python -m venv .venv

Activate virtual environ:
  .\.venv\Scripts\Activate.ps1

Install Playwright:
  pip install playwright
  playwright install chromium

## Configuration

Copy 'config.example.json' and rename to:
  config.json

Add your own Discord webhook URL and configure desired delay periods.

## Usage

Run the monitor with:

  python stock_bot.py

The monitor will periodically check each retailer and display its current stock status.

When a retailer changes to "IN STOCK", the program sends a Discord notification and plays an audible alert.

## Disclaimer

This project is intended for personal and educational use.

It monitors publicly accessible product pages for availability and does not automatically purcahse products. Checkout and purchasing remain manual.

Retailer websites may change their page structure at any time, which can cause individual stock checks to stop working.

## Known Issues

Target detects repeated polling as bot activity and requests verification.
Continued polling of GameStop site caused IP to be blocked
