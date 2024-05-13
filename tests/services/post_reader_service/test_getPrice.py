from app.services.post_reader_service import PostReaderService


def test_getPrice():
    caption = "قیمت💰: 448 توما"
    assert PostReaderService.getPrice(caption) == 448000
    caption = "قیمت💰: 448 توما\nقیمت💰: 448 توما"
    assert PostReaderService.getPrice(caption) == 448000
    caption = "قیمت💰: 448 توما\nقیمت💰: 448 توما\nقیمت💰: 448 توما"
    assert PostReaderService.getPrice(caption) == 448000
    caption = "قیمت💰: 448 تومان موجودی 10 عدد"
    assert PostReaderService.getPrice(caption) == 448000
    caption = "قیمت💰: 4.48 تومان موجودی 10 عدد"
    assert PostReaderService.getPrice(caption) == 4480
    caption = "قیمت💰: 4,48 تومان موجودی 10 عدد"
    assert PostReaderService.getPrice(caption) == 448
