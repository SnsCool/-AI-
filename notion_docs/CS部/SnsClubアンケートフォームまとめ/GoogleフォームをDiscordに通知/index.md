# GoogleフォームをDiscordに通知

**種類**: 📄 ページ
**階層**: 3
**更新日時**: 2026-01-14 12:09

---

## コンテンツ

## ①赤枠内の「・・・」をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/abb134b1-9b4d-4391-8588-b704f2321bc9/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.21.51.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=70c1bec5892d407b5991a47222d7c51c7df170b8d2a8234ce090fadc58920c1c&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ②Apps Scriptを選択
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/0e7e9b0f-10c1-4181-b7fd-4d255200815a/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.22.53.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=4b506b491d36f464fe4f0a0f523ecaf8e3955519cf761768e9db332ed2554b02&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

③元々入っている赤枠内のコードを削除し、以下のコードを貼り付け
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/c17ce00b-d28a-438d-a478-14ac538898c8/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.24.30.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=3268cbe4a99f3608d9005b01da65fc6807d11feee816663e14bf093d70d3ceee&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

↓スレッドに送信するパターンのコード
```javascript
  // Discord のWebhook URLとスレッドID
  var discordWebhookUrl = "Webhook URL";
  var threadId = "スレッドID";


function getForm(e) {
  var formResponses = e.response.getItemResponses();
  var email = e.response.getRespondentEmail(); // メールアドレスの取得

  // メールアドレスが取得できなかった場合、最初の質問の回答を「回答者」として使用
  if (!email && formResponses.length > 0) {
    var firstResponse = formResponses[0].getResponse();
    email = firstResponse ? firstResponse : "ユーザー";
  }

  var contents = "";
  var size = formResponses.length;

  for (var i = 0; i < size; i++) {
    var itemResponse = formResponses[i];
    try {
      var question = itemResponse.getItem().getTitle();
      var answer = itemResponse.getResponse();
      contents += "【" + question + "】\n" + answer + "\n\n";
    } catch (ex) {
      console.log(i + "でエラーが発生しました。");
      console.log(ex);
    }
  }

  var webhookUrlWithThread = `${discordWebhookUrl}?thread_id=${threadId}`;

  var title = "フォームの入力がありました。\n";
  var message = title + contents;

  // Discord は1メッセージあたり最大2000文字なので、2000文字以上の場合は分割する
  var maxLength = 2000;
  var messages = [];
  
  for (var i = 0; i < message.length; i += maxLength) {
    messages.push(message.substring(i, i + maxLength));
  }
  
  // 分割された各チャンクを順次送信
  messages.forEach(function(chunk) {
    var payload = {
      "content": chunk
    };
    UrlFetchApp.fetch(webhookUrlWithThread, {
      method: "POST",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
  });
}

```



↓チャンネルに送信するパターンのコード
```javascript
  // Discord のWebhook URLとスレッドID
  var discordWebhookUrl = "Webhook URL";



function getForm(e) {
  var formResponses = e.response.getItemResponses();
  var email = e.response.getRespondentEmail(); // メールアドレスの取得

  // メールアドレスが取得できなかった場合、最初の質問の回答を「回答者」として使用
  if (!email && formResponses.length > 0) {
    var firstResponse = formResponses[0].getResponse();
    email = firstResponse ? firstResponse : "ユーザー";
  }

  var contents = "";
  var size = formResponses.length;

  for (var i = 0; i < size; i++) {
    var itemResponse = formResponses[i];
    try {
      var question = itemResponse.getItem().getTitle();
      var answer = itemResponse.getResponse();
      contents += "【" + question + "】\n" + answer + "\n\n";
    } catch (ex) {
      console.log(i + "でエラーが発生しました。");
      console.log(ex);
    }
  }

  var webhookUrlWithThread = `${discordWebhookUrl}`;

  var title = "フォームの入力がありました。\n";
  var message = title + contents;

  // Discord は1メッセージあたり最大2000文字なので、2000文字以上の場合は分割する
  var maxLength = 2000;
  var messages = [];
  
  for (var i = 0; i < message.length; i += maxLength) {
    messages.push(message.substring(i, i + maxLength));
  }
  
  // 分割された各チャンクを順次送信
  messages.forEach(function(chunk) {
    var payload = {
      "content": chunk
    };
    UrlFetchApp.fetch(webhookUrlWithThread, {
      method: "POST",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
  });
}

```
## ④赤枠内にWebhook URLとスレッドIDを貼り付け
※チャンネルに送信するパターンのコードの場合、スレッドIDの記載箇所がありません

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/e92eac29-09f6-4cfd-8d22-17ef54917df8/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.48.53.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=936762b1eefc44982060507c70392ac0f9ee47831d5855b81cb54334f7339633&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

### Webhook URLの取得方法
チャンネル名の右の⚙️をクリック
↓
連携サービス
↓
ウェブフック
↓
新しいウェブフック
↓
作成したウェブフックをクリック
↓
名前を変更、保存
↓
ウェブフックURLをコピーをクリック

### スレッドIDの取得方法
対象のスレッドを右クリック
↓
スレッドIDをコピー

↓のような形式で、””は削除せずに貼り付け
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/be602852-148a-49b1-902d-dfb64ebb5348/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.57.36.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=d7df7aa6d785bae28d61afb7611702dbe2d0dbda6f5f9e93e1cd202abb4a2e1b&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑤保存ボタンをクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/82dc6307-4671-4d90-94c6-8ff4b7c65867/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.58.11.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=f2e32bdaff59bfb24b65ac629e265fb5de52c2bcc09d8378d34bdfde87e7b995&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑥左側メニューの目覚ましマークをクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/14e73a0b-6757-4dc8-85aa-4841429f6c12/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.59.07.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=55af6dae2595320a4bc41badf13ff8589c78352d9ab4a7167a178b34d85ce826&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑦右下のトリガーを追加をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/b02d3a38-af9c-4c57-8447-b5b4c467103b/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.59.57.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=9f63cf713fd3d31df27f2737998ecfa47f862f086697a65b79a3a661d3cb702d&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑧以下の内容に変更をし、保存をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/6701b62f-fae3-48d8-9719-faaaa7ec091d/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.00.48.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=8a0a10d5b28c5e458685c613ced5d7f443e9f8d3e74cd9fb3d8cb94fb37362bb&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


## ⑨以下の手順で進めれば完了です！
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/03113e57-b9f0-4302-9d45-eaf75833c142/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.05.40.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=7e07d76e7cc1df3fa7bf35b1960fa430f56ee60a07c40cce27fb87e9a89946ea&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/0dea360a-fb7c-4dbe-983e-961a05b519dc/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.08.35.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466TZYOHDIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T001716Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEgaCXVzLXdlc3QtMiJHMEUCIQDy6LB00TdScmoaQD2MovOdMuAqSM5MV6rgOOKq9f8XdQIgQdETzwSx47KHdaILzZc%2F%2F%2FtF5PkF73gMV8mPdtvgWoUq%2FwMIERAAGgw2Mzc0MjMxODM4MDUiDAQFFJhMOb%2ByD8e7iircA5mjjT97LPSHQD2YFLJopDkXEG%2BIpn2v%2BiJ1wwZ7HpGPovjfuzZnyAeq6h2wEQXaiWR%2BPapzgPI7k%2BBThAT%2BkZFbnnvqByzCivyNK83YXEGp4bE3lGbgOZSwa5X6EU%2F5FsksP0VfdxovngZOI4uXRalApu2S9P9V70%2FtXem22%2BQqU%2BlBnaKxbAeolSH%2B9LrFCQQCmfJ4LNfuQHOxaC3%2FE5OS%2BQOVRBsQGq6nbUiIzzCqCyA6OMvSXzwNx5WSjynmpGMrbyKHCzOKpG0XZF4XwIKswOAGseFRl5h5E1c6B1QL18ILptgubr9LgdFDRXTTogYnaza6KaaPy19Jr1rLlZ088dhyk9vQXpEhPNNs%2Fndk7eje2PPPkLFJSEbWhqmNtoMuxPy%2Bw2rol77CGj0vdJTAT8bgfh9Xa9Wl9iQjcIMlTgilBgTwzWrUO%2BgqYLYftY9oBVlSzcueh2c2B8vEVoCcgU8TZpps38GypcnjuINWYZBdQwUd7ytiXVoEki5KjL%2BzHG9VUFkBUhtjb07HbTmNEreYkq9IwDf3l0Auo9l01ibIFnt8WBDaV3CUR%2Fs7feAXKMFcvwdyxTKEPWSi%2FSSDpyVhGoydEnaYvP37rujjtTxhD76Cgrh4UrqMMPa7m8sGOqUBVkBY1yEFDgeP99s9hvuPowbZSPXtCGXbsC8z78RFQ5h8tuKtbZtIzKq496zsvEvDDcvvDa%2B0p3aBRmT51yiFWwH39USl03d2AYwj68lu57XcOrOlz1v4WpkPk3DTzfgv%2BwsXdoR6aKTlY9kwJ8rdheUhpOhq%2BT7eEhiVjvGhqllZwWerFpbrLa5fwGNJkuz17nTmuB%2FG0YKDXC6gaUGCA08f1nF0&X-Amz-Signature=d4164635f20d1ca8c1ff327d6c97186a95439baaee40a11cc1d293b00cec37fa&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


---

## 子要素一覧

(子要素なし)

---
*Generated: 2026-01-14 12:09*
