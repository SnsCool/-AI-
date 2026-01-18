# GoogleフォームをDiscordに通知

**種類**: 📄 ページ
**階層**: 2
**更新日時**: 2026-01-14 12:09

---

## コンテンツ

## ①赤枠内の「・・・」をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/abb134b1-9b4d-4391-8588-b704f2321bc9/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.21.51.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=f4050741e86b1fe1c165cb7b1c6662788cd0df5fd1ada0dd92b3b816cb663b92&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ②Apps Scriptを選択
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/0e7e9b0f-10c1-4181-b7fd-4d255200815a/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.22.53.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=6480b6819b8dc6485be01ca719a44807500f4864caa8eb3ff61d2fd82a71f1f6&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

③元々入っている赤枠内のコードを削除し、以下のコードを貼り付け
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/c17ce00b-d28a-438d-a478-14ac538898c8/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_14.24.30.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=f1c8de6d055448c05f023fad90d14d962184756f810bc11290a87eeff644af4c&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

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

![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/e92eac29-09f6-4cfd-8d22-17ef54917df8/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.48.53.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=54fffbba5789473186f9540a9390d0fbafae9335aa9565ae559ebe3636a265a8&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/be602852-148a-49b1-902d-dfb64ebb5348/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.57.36.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=98093055ff26a28bc5c64e8ded4476a1ca89de00da6284449c983028a125c5bf&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑤保存ボタンをクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/82dc6307-4671-4d90-94c6-8ff4b7c65867/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.58.11.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=e3bd1250cdfea7ca437295e92fc23d389541b88d93f6af3d71effd9b9eed001e&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑥左側メニューの目覚ましマークをクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/14e73a0b-6757-4dc8-85aa-4841429f6c12/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.59.07.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030745Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=c21ff81688d7b76bba59e5040e2812e086890c4d531eca7a264f6525a5b8a28e&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑦右下のトリガーを追加をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/b02d3a38-af9c-4c57-8447-b5b4c467103b/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_16.59.57.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030746Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=a286e785be07e55b2741ca0132d03a86d645b37303c93b93c7891e4e412a96ae&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)

## ⑧以下の内容に変更をし、保存をクリック
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/6701b62f-fae3-48d8-9719-faaaa7ec091d/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.00.48.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030746Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=4073f01155dbbe715a984478c75d0f38b67128b6f9770f3a52c7550cbbcf975d&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


## ⑨以下の手順で進めれば完了です！
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/03113e57-b9f0-4302-9d45-eaf75833c142/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.05.40.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030746Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=e3cba66ab6a685e0b604f0a187a0e7884a3ec88f6511e0310b330dabf7402650&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


![](https://prod-files-secure.s3.us-west-2.amazonaws.com/89e6f4ed-ae9b-4395-871a-0c505f895ff0/0dea360a-fb7c-4dbe-983e-961a05b519dc/%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%82%B7%E3%83%A7%E3%83%83%E3%83%88_2025-02-23_17.08.35.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466VIDABRIS%2F20260114%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260114T030746Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEEsaCXVzLXdlc3QtMiJHMEUCIFv%2BRcQJ%2FfBiYEI10txIujNF26Iv9CXIs5ubA0MTr1erAiEAjybCwa9FGvDBPW89KEDxD6iG%2Bzw5JSHk6m0cRpExDIUq%2FwMIFBAAGgw2Mzc0MjMxODM4MDUiDFZaQc60vq5zrTbidircA8oaONSbpuxSfnW8Z%2Fce8Jp4g3U1DYLyA%2FhPFDsIdZmw5vhvA%2BEFf7x7bVtC4t4JjuYHaUU%2BxBJ36b9oZ07OSiVcPZPnJ25yjLci3U1cdCtZfKvunhsrFQPIEkBanUaU1HGvFrrRa9PdaxB2iQ8Vv%2BhUq4k%2FggaycXRkW6DjdaIvSsbeh9zx5bL7Q9is%2BNT3NlFtOGnwoSkmkrSiXaNQDwlgqrUxIpcz54bz%2F7DTzw%2FDtTi0e3RETN1zwAZAXSA2O7nFG33Q5m5GfU65k36gHbz1k05aUbie%2Fi4apwpKcvJ5D0dY8R%2FTmY3Di36tW1nJ8W6eg4%2BLfo8rA%2BeaxJvLlKRZvWPYyuh%2BWOhXFZgcRiw8FDKFNrEK5rkWYXKA%2Fzms6xgej6FNOgqZqjKc%2BzKdBgAJuxceALZ3kkyB4WgmQxmMTKun%2BiEKSHTJUF3stP2Z%2FbGUlLWD9TQO9bPLW7NS9DggcFtHe6M150yBF0shCAH5AAZW%2B2zn2lwpWG3NJGiVrX1jDox7pZJRD3aLfbCU1B1x8v%2FLobTWygWSpcHcXVdYi21bvnpHFfrbwoMGGblAYJnI43N%2B%2BZueW%2FqmPx4q6w6q90nnmZ3lb4O%2Bkkup3hHWbq0X8AeCqeus2JLuMMqPnMsGOqUBrQj05nadF1efGDGuBQttL7jFow9UdYUHmP2g6wUWL%2BLztP8xOF34o2If8dFxSOaJkMbGSPy3Krg2EUfGfdecUCq5UT9XEkPpKlgJuRM6kPjNZcL1V8b5Ne6xa%2BwBxUu95aWPCdlWMryTrabWy%2By8lD3FaU16u%2BHlxVRIlVzU2wlwEmiGMu0VuCpYrIPJh3mYZBaAjhi7vDj8%2FaMfzRX9BN3YCdbe&X-Amz-Signature=a3a9ec008a6f536dea8f92be7dfbf7a78bab538b330e73e1702f3f1558233de7&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)


---

## 子要素一覧

(子要素なし)

---
*Generated: 2026-01-14 12:09*
