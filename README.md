# AutoDelete Telegram Bot 🤖⏳

![Banner](https://te.legra.ph/file/e0e4b5df761aa6e9916b2.png)

A Telegram bot that automatically deletes messages after a specified time period.

## Features ✨
- Set custom deletion time per group
- Whitelist/Blacklist support
- MongoDB persistence
- Health check endpoint
- Koyeb/Railway/VPS compatible

## Deployment 🚀

### Environment Variables
| Variable | Description |
|----------|-------------|
| `API_ID` | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | From [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `DATABASE_URI` | MongoDB connection string |
| `PORT` | Web server port (default: `8080`) |

### Koyeb Deployment
[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/yourrepo/AutoDelete&branch=main)

```bash
# Start command:
python main.py
```

### Local Development
```bash
git clone https://github.com/yourrepo/AutoDelete
cd AutoDelete
pip install -r requirements.txt

# Create .env file
echo "API_ID=your_id" >> .env
echo "API_HASH=your_hash" >> .env
echo "BOT_TOKEN=your_token" >> .env
echo "DATABASE_URI=your_mongodb_uri" >> .env

python main.py
```

## Bot Commands 🛠️
- `/auth` - Enable bot in current group (Admin only)
- `/settime [seconds]` - Set auto-delete delay
- `/status` - Show current settings
- `/debug` - Technical information

## Database Structure 🗃️
```javascript
// Messages collection
{
  chat_id: Number,
  message_id: Number,
  time: Number, // Unix timestamp
  saved_at: Date
}

// Groups collection 
{
  chat_id: Number,
  active: Boolean,
  delete_after: Number,
  title: String,
  last_updated: Date
}
```

## Support 💬
For issues or questions, join our [Support Group](https://t.me/Annihilusop_bot)