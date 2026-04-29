#!/bin/bash

# Ensure cron is running
service cron start

# Add the cron job to run at 9:00 AM every day
# We pass environment variables to the cron environment so python can access them
echo "0 9 * * * cd /app && /usr/local/bin/python pipeline.py --count 1 >> /app/output/cron.log 2>&1" > /etc/cron.d/homvyx-cron

# Give execution rights on the cron job
chmod 0644 /etc/cron.d/homvyx-cron

# Apply cron job
crontab /etc/cron.d/homvyx-cron

echo "Homvyx Docker Container started successfully."
echo "Cron scheduled for 9:00 AM EST every day."
echo "Waiting for execution..."

# Keep the container running
tail -f /dev/null
