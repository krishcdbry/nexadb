/**
 * YCSB StringByteIterator
 *
 * A ByteIterator backed by a String.
 */
package site.ycsb;

import java.nio.charset.StandardCharsets;

public class StringByteIterator extends ByteIterator {

    private final String str;
    private int offset;

    /**
     * Create a StringByteIterator from a String.
     */
    public StringByteIterator(String s) {
        this.str = s;
        this.offset = 0;
    }

    @Override
    public boolean hasNext() {
        return offset < str.length();
    }

    @Override
    public Byte next() {
        byte[] bytes = str.substring(offset, offset + 1).getBytes(StandardCharsets.UTF_8);
        offset++;
        return bytes[0];
    }

    @Override
    public long bytesLeft() {
        return str.length() - offset;
    }

    @Override
    public byte[] toArray() {
        return str.substring(offset).getBytes(StandardCharsets.UTF_8);
    }

    @Override
    public String toString() {
        return str.substring(offset);
    }

    /**
     * Reset the iterator to the beginning.
     */
    public void reset() {
        offset = 0;
    }
}
