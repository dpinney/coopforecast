from flask.views import View


def transform_timeseries_df_for_highcharts(df, value=None):
    """
    Highcharts uses milliseconds, not seconds, so multiply by 1000. And
    then zip with the load value.
    """
    highcharts_array = []
    for i, row in df.iterrows():
        highcharts_array.append([row["timestamp"].timestamp() * 1000, row[value]])
    return highcharts_array


class RenderTemplateView(View):
    def __init__(self, template_name):
        self.template_name = template_name

    def dispatch_request(self):
        return render_template(self.template_name)

    @classmethod
    def view(cls, name, template=None):
        if template:
            return self.as_view(name, template_name=template)
        else:
            template_name = name + ".html"
            return cls.as_view(name, template_name=template_name)
