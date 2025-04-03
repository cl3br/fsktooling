import fsklib.model as model

class RSC:
    @staticmethod
    def get_discipline_code(category: model.Category) -> str:

        code = "FSK" + category.gender.ODF() + category.type.ODF()
        code += "-" * (12 - len(code))
        code += category.level.ODF()
        code += "-" * (20 - len(code))
        code += "%02d" % category.number if category.number else "--"

        # add trailing dashes (discipline code always consists of 34 characters)
        code += "-" * (34 - len(code))
        return code

    @staticmethod
    def get_discipline_code_with_segment(category: model.Category, segment: model.Segment, segment_number: int) -> str:

        code = RSC.get_discipline_code(category)
        segment_code = segment.type.ODF()
        assert len(segment_code) <= 4
        return code[:-12] + segment_code + (4 - len(segment_code)) * '-' + "%06d--" % (100 * segment_number)
