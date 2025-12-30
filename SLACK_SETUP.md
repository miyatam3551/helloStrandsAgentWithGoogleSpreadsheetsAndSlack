# Slack メンション機能のセットアップガイド

このガイドでは、Slack でボットをメンションした際に AI エージェントが自動応答する機能の設定方法を説明します。

## 📋 前提条件

- Terraform で Lambda 関数と API Gateway がデプロイ済みであること
- Slack ワークスペースの管理者権限があること
- Slack Bot Token が Parameter Store に保存されていること

## 🔧 Slack App の設定

### 1. Slack App の作成（既存の場合はスキップ）

1. [Slack API](https://api.slack.com/apps) にアクセス
2. 「Create New App」→「From scratch」
3. アプリ名とワークスペースを選択

### 2. Bot Token Scopes の設定

「OAuth & Permissions」→「Scopes」で以下の権限を追加：

**必須権限:**
- `app_mentions:read` - メンションを受け取る
- `chat:write` - メッセージを送信する
- `chat:write.public` - 公開チャンネルにメッセージを送信する

### 3. Event Subscriptions の設定

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

### 4. ワークスペースにインストール

1. 「Install App」に移動
2. 「Install to Workspace」をクリック
3. 権限を確認して「許可する」をクリック

### 5. Bot をチャンネルに追加

メンションを受け取りたいチャンネルで：

```
/invite @your-bot-name
```

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

## 🐛 トラブルシューティング

### Request URL の検証が失敗する

**症状:** Slack が "Your URL didn't respond with the value of the challenge parameter" と表示

**原因:**
- Lambda 関数がデプロイされていない
- API Gateway のエンドポイントが間違っている
- Lambda 関数のチャレンジレスポンス処理にエラーがある

**解決方法:**
```bash
# Lambda のログを確認
aws logs tail /aws/lambda/hello-agent --follow

# API エンドポイントを確認
cd terraform
terraform output slack_events_endpoint
```

### ボットがメンションに応答しない

**症状:** メンションしてもボットが反応しない

**原因:**
- Event Subscriptions で `app_mention` が設定されていない
- ボットがチャンネルに追加されていない
- Lambda 関数にエラーが発生している

**解決方法:**
1. ボットをチャンネルに追加: `/invite @your-bot-name`
2. Lambda ログでエラーを確認:
   ```bash
   aws logs tail /aws/lambda/hello-agent --follow
   ```

### "retry_after" エラーが発生する

**症状:** Slack が同じイベントを何度も再送する

**原因:** Lambda の処理に 3 秒以上かかっている

**解決方法:**
- Slack Events API は 3 秒以内の応答を期待しています
- Lambda がすぐに 200 OK を返し、バックグラウンドで処理を継続するように実装されています
- 現在の実装では、応答は同期的に返されるため、AI の処理が遅い場合は問題が発生する可能性があります

**改善案（将来的に実装可能）:**
- Lambda を非同期で呼び出し、すぐに 200 OK を返す
- Step Functions または SQS を使った非同期処理

## 🔐 セキュリティ

### Signing Secret による検証（推奨）

Slack Events API のリクエストが正当なものであることを検証するため、Signing Secret を使用することを推奨します。

**実装方法:**
1. Slack App の「Basic Information」から「Signing Secret」を取得
2. Parameter Store に保存:
   ```bash
   aws ssm put-parameter \
     --name "/your-prefix/slack-signing-secret" \
     --value "your-signing-secret-here" \
     --type "SecureString" \
     --overwrite
   ```
3. Lambda 関数で検証ロジックを追加（将来的な改善）

## 📚 参考リンク

- [Slack Events API ドキュメント](https://api.slack.com/apis/connections/events-api)
- [app_mention イベント](https://api.slack.com/events/app_mention)
- [Slack Bot Token スコープ](https://api.slack.com/scopes)
