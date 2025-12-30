## 🔧 Slack App の設定

### Event Subscriptions の設定

1. 「Event Subscriptions」に移動
2. 「Enable Events」をオンにする
3. **Request URL** を設定：

   ```
   https://your-api-endpoint.execute-api.ap-northeast-1.amazonaws.com/slack/events
   ```

   エンドポイント URL を取得するには：
   ```bash
   cd terraform
   terraform output slack_events_endpoint
   ```

4. URL を入力すると、Slack が検証リクエストを送信します
   - ✅ "Verified" と表示されれば成功

5. 「Subscribe to bot events」で以下のイベントを追加：
   - `app_mention` - ボットがメンションされた時

6. 「Save Changes」をクリック


## ✅ 動作確認

Slack チャンネルでボットをメンションしてみましょう：

```
@your-bot-name こんにちは！
```

ボットが応答すれば成功です！

### テスト例

**基本的な会話:**
```
@your-bot-name 今日の天気はどうですか？
```

**スプレッドシートへの追加:**
```
@your-bot-name プロジェクト名「新機能開発」をスプレッドシートに追加してください
```

**Slack 通知:**
```
@your-bot-name #general チャンネルに「テスト完了」と通知してください
```

**複数ツールの連携:**
```
@your-bot-name 新しいプロジェクト「API改善」をシートに追加して、#team チャンネルに通知してください
```
