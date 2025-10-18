class PCMWorkletProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const [input] = inputs;
    if (input && input[0]) {
      const channelData = input[0];
      // Clone the channel data so that it can be transferred safely to the main thread.
      this.port.postMessage(channelData.slice());
    }
    return true;
  }
}

registerProcessor("pcm-worklet-processor", PCMWorkletProcessor);
