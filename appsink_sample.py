import argparse
import logging
import typing

import gi
import gstreamer.utils
import numpy as np
from gstreamer import GstVideo, GstApp

gi.require_version("Gst", "1.0")
gi.require_version("GstBase", "1.0")

from gi.repository import Gst

logger = logging.getLogger(__name__)


def on_buffer(sink: GstApp.AppSink, user_data: typing.Any) -> Gst.FlowReturn:
    sample = sink.emit("pull-sample")

    if not isinstance(sample, Gst.Sample):
        return Gst.FlowReturn.ERROR

    buffer = sample.get_buffer()  # Gst.Buffer
    logger.debug("PTS: %d, DTS: %d", buffer.pts, buffer.dts)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
    caps_format_string = caps_format.get_value("format")
    assert caps_format_string == "RGB"

    # GstVideo.VideoFormat
    video_format = GstVideo.VideoFormat.from_string(caps_format_string)

    w, h = caps_format.get_value("width"), caps_format.get_value("height")
    c = gstreamer.utils.get_num_channels(video_format)

    buffer_size = buffer.get_size()
    shape = (h, w, c) if (h * w * c == buffer_size) else buffer_size
    array = np.ndarray(
        shape=shape,
        buffer=buffer.extract_dup(0, buffer_size),
        dtype=gstreamer.utils.get_np_dtype(video_format),
    )

    array = np.squeeze(array)  # remove single dimension if exists

    logger.info(
        f"Received {type(array)} with shape {array.shape} of type {array.dtype}"
    )

    return Gst.FlowReturn.OK


def consume_rtsp(rtsp_url: str):
    logger.debug("Consume %s", rtsp_url)

    pipeline_command = """rtspsrc location={rtsp_url}
        ! decodebin
        ! videoconvert
        ! video/x-raw,format=RGB
        ! queue
        ! appsink emit-signals=true name=appsink
        """.format(
        rtsp_url=rtsp_url
    )
    pipeline = Gst.parse_launch(pipeline_command)
    appsink = pipeline.get_by_name("appsink")

    appsink.connect("new-sample", on_buffer, None)

    pipeline.set_state(Gst.State.PLAYING)

    bus = pipeline.get_bus()
    try:
        while True:
            msg = bus.poll(Gst.MessageType.ANY, int(100 * 1e6))

            if msg is None:
                continue

            t = msg.type
            if t == Gst.MessageType.EOS:
                logger.info("EOS")
                break
            elif t == Gst.MessageType.ERROR:
                err, debug = msg.parse_error()
                logger.error("Error: %s, %s", err, debug)
                break
            elif t == Gst.MessageType.WARNING:
                err, debug = msg.parse_warning()
                print("Warning: %s, %s", err, debug)
            elif t == Gst.MessageType.STATE_CHANGED:
                pass
            elif t == Gst.MessageType.STREAM_STATUS:
                pass
            elif t == Gst.MessageType.STREAM_START:
                pass
            elif t == Gst.MessageType.PROGRESS:
                pass
            elif t == Gst.MessageType.ASYNC_DONE:
                pass
            elif t == Gst.MessageType.NEW_CLOCK:
                pass
            elif t == Gst.MessageType.TAG:
                pass
            else:
                logger.warn("Unknown message: %s: %s", t, msg)
                pass
    except KeyboardInterrupt:
        pipeline.send_event(Gst.Event.new_eos())
        while True:
            msg = bus.poll(Gst.MessageType.ANY, int(100 * 1e6))

            if msg is None:
                continue

            t = msg.type
            if t == Gst.MessageType.EOS:
                break
    finally:
        pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rtsp_url", type=str)
    parser.add_argument("-d", "--debug", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    consume_rtsp(args.rtsp_url)
