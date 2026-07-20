try:
    from . import lucky_number_tool as lnt
    from . import web_search_tool as wst
    from . import check_python_code_tool as cpct
    from . import student_record_tools as srt
    from . import datetime_tool as dtt
    from . import knowledge_search_tool as kst
except ImportError:
    import lucky_number_tool as lnt
    import web_search_tool as wst
    import check_python_code_tool as cpct
    import student_record_tools as srt
    import datetime_tool as dtt
    import knowledge_search_tool as kst


tools = [
    lnt.lucky_number_tool,
    wst.web_search_tool,
    cpct.check_python_code_tool,
    srt.save_student_evaluation_tool,
    srt.get_student_record_tool,
    dtt.current_datetime_tool,
    kst.knowledge_search_tool,
]
