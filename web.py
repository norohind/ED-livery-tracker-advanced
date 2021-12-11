from model import model
import json
import falcon
import os

model.open_model()
activity_table_html_template = """<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <script src="/js/json2htmltable.js"></script>
         <script type="text/javascript">
            window.addEventListener("load", () => {
                document.body.appendChild(buildHtmlTable({items}));  // build table

                var table = document.querySelector("body > table")
                var header = table.rows[0]

                for (var i = 0, cell; cell = header.cells[i]; i++){
                    if (cell.innerText.includes('{target_column_name}')){
                       var target_column_id = i;
                       break;
                    }
                }
                
                if (target_column_id == null) {  // don't to anything if no action_id in the table
                    return;
                }

                for (var i = 1, row; row = table.rows[i]; i++) {  // append to action_id filed onclick action
                   row.cells[target_column_id].innerHTML = '<td><a href="{link}">{original_value}</a></td>'.replace('{link}', '{target_new_url}' + table.rows[i].cells[target_column_id].innerText).replace('{original_value}', table.rows[i].cells[target_column_id].innerText);
                }
            })
        </script>
        <link type="text/css" rel="stylesheet" href="/js/table_styles.css">
    </head>
    <body>
    </body>
</html>"""


class Activity:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response) -> None:
        resp.content_type = falcon.MEDIA_JSON

        args_activity_changes = {
            'limit': req.params.get('limit', 10),
            'high_timestamp': req.params.get('before', '3307-12-12'),
            'low_timestamp': req.params.get('after', '0001-01-01')
        }

        try:
            resp.text = json.dumps(model.get_activity_changes(**args_activity_changes))

        except Exception as e:
            print(f'Exception occurred during executing Activity request:\n{e}')
            raise falcon.HTTPInternalServerError(description=str(e))


class ActivityHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response) -> None:
        Activity().on_get(req, resp)
        table_in_json: str = resp.text
        resp.content_type = falcon.MEDIA_HTML

        resp.text = activity_table_html_template.replace(
            '{items}', table_in_json
        ).replace('{target_column_name}', 'ActionId').replace('{target_new_url}', '/diff/')
        # what? f-strings? .format? never heard about them


class ActivityDiff:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:

        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(model.get_diff_action_id(action_id))


class ActivityDiffHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = activity_table_html_template.replace(
            '{items}', json.dumps(model.get_diff_action_id(action_id)))


app = falcon.App()
app.add_route('/api/livery', Activity())
app.add_route('/api/diff/{action_id}', ActivityDiff())

app.add_route('/livery', ActivityHtml())
app.add_route('/diff/{action_id}', ActivityDiffHtml())

application = app  # for uwsgi

if __name__ == '__main__':
    import waitress

    app.add_static_route('/js', os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'js'))
    app.add_static_route('/', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
    waitress.serve(app, host='127.0.0.1', port=9486)
