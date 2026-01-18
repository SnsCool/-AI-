# GoogleフォームをDiscordに通知

**種類**: 📄 ページ
**階層**: 3
**更新日時**: 2026-01-14 12:09

---

## コンテンツ

## ①赤枠内の「・・・」をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/abb134b1-9b4d-4391-8588-b704f2321bc9/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.21.51.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=85113a0c27c7ee1faf11e42fefb675d3f4d898b99ce357f32b2e3306524ead78&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ②Apps Scriptを選択
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/0e7e9b0f-10c1-4181-b7fd-4d255200815a/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.22.53.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=85a8dc9a388f889ab0f7e8f0234d4384bc59107844c482cb4c0bc2e90705f5b2&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

③元々入っている赤枠内のコードを削除し、以下のコードを貼り付け
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/c17ce00b-d28a-438d-a478-14ac538898c8/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.24.30.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=75020633472a3299924b5e29608ceefb7c1c873a71e810ac1179efd80584ed0b&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

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

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/e92eac29-09f6-4cfd-8d22-17ef54917df8/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.48.53.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=55c2a18114926184039fab9aeec69311a868e6d6dd24be413b00240cbb8c7383&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/be602852-148a-49b1-902d-dfb64ebb5348/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.57.36.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=f88a1e7e90e9e5ca2dc791ec8cf0af7ebcf2c33475e53be8f03034003c721250&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑤保存ボタンをクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/82dc6307-4671-4d90-94c6-8ff4b7c65867/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.58.11.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=cb87c025675535fcbca09a288851b0c376447a96af5207fed9948bac1c0a788e&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑥左側メニューの目覚ましマークをクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/14e73a0b-6757-4dc8-85aa-4841429f6c12/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.59.07.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=0500a0ef9283347806ce3202566a31af93fdeb2540717a6d8c91516bb58f6c38&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑦右下のトリガーを追加をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/b02d3a38-af9c-4c57-8447-b5b4c467103b/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.59.57.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=fcfcaa52e54b1b469e8c401f8753e8ab675cb8699bfd8f79747aaac2a93dfc5b&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑧以下の内容に変更をし、保存をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/6701b62f-fae3-48d8-9719-faaaa7ec091d/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.00.48.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=74863480527c1ef0cc8a9a8142980a1ac2d1d11beb517e2c31235d2a8ff72a59&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


## ⑨以下の手順で進めれば完了です！
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/03113e57-b9f0-4302-9d45-eaf75833c142/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.05.40.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=080927392cd4f06da99f522ef479565cc427008502b0201ff598a5e0766a178f&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/0dea360a-fb7c-4dbe-983e-961a05b519dc/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.08.35.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UQ6HVHXF%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030732Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCICebs1qoP706qX3iW%2Fw7yg2IE%2Bq8Te2BbzUAqTycYndAAiEAk90puV6Q1EiKnEb%2BXOJDHFyIqSo4W3JSoisfVLBiY1Mq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDCKNTbjD4VBfIbB62yrcA8890lfANJePswcMui2QD97AdN98ewH4oiYaL01%2FexSIDTVpKnPJ046w0dHiThX6zbSoegTKIYvKwn0r7Wy2PBPo%2B%2Fxf7tpJEaxEUJxPEdojc%2BetC4x3l%2FU%2F%2Fg41fB6e6bI5esKFY1dCuNNEKHtoPbPdl5O31UYJ%2BjkEPauFIPS%2F6OAxB7ibXEjOwy%2BbPP0KHKktqbL4OJNVroCK5NnDqBk4OXyjEDZyHziybUClPNiBs4xhcfUDNEddH2n9HQELUk7YDS5cb0GFIDSOa4SQ00ddl9AvYk9sXo2lrO3gpAYxh10xktYF1E63C4YDjQjGEK9V2fHDlmb4k%2B4UHyPeEA%2BabpQfAIkjyYBPngMruA9nCZB4jMq4ezTieGCp5wBSzln5uPLbLbE3bfzIlRchyhWUI1Vsz0%2FIPdI%2B6dAqbIfTkhQGtzgGPOEAbBGxEZaXhyr1J600EEjtzlmIAEQdAJlZTrLin45RjGVOV8Zxz1ilv7AEHnBOtAqvDux9GaBvpuSmWihnRuK%2FD9lf%2FveRlQMPRDE4Zp%2B2vuygLZyPqnHf2cgRmQ%2Fo68QB2cpk59Qcd3W7N1wZLBUnvQiohgaCcJjv%2B%2BnheaBKhs%2ByLnGO40zQy3COgFzZvZiccPaeMMWPnMsGOqUBBBaJ2JG08A5IbFC9lM3A0esd1z1T2BJd5qDbpFXTBQKN1dZxkkFKohfgVqztHpTWc2aApVPpPe%2FA%2Fj7S9i6C%2FBQMBtRB14NoRt098cZ5%2FvrVR0vj7om%2BzJtfI2Bq%2BOpZcFDbfiwBfghiqVRVgl6bXnyCGFRhD4UwIGi4sJXFhXS9SVu%2BjlxHhXQ6LE%2FdCZuTfocKJNo5Q0ENHo0mqcZZr457j9RM&X-Amz-Signature=42a6c545171f0b541d8b72da70680ffdf467d2dd995ca1bc752c073822f256c7&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


---

## 子要素一覧

(子要素なし)

---
*Generated: 2026-01-14 12:09*
