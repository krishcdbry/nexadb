/**
 * YCSB ByteIterator
 *
 * Abstract iterator for byte sequences used in YCSB.
 */
package site.ycsb;

import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;

public abstract class ByteIterator implements Iterator<Byte> {

    /**
     * @return the next byte in the sequence
     */
    @Override
    public abstract Byte next();

    /**
     * @return the number of bytes remaining in the sequence
     */
    public abstract long bytesLeft();

    /**
     * @return true if there are more bytes to read
     */
    @Override
    public boolean hasNext() {
        return bytesLeft() > 0;
    }

    /**
     * @return the remaining bytes as a byte array
     */
    public byte[] toArray() {
        long left = bytesLeft();
        if (left != (int) left) {
            throw new ArrayIndexOutOfBoundsException("Too many bytes to fit in an array");
        }
        byte[] ret = new byte[(int) left];
        for (int i = 0; i < ret.length; i++) {
            ret[i] = next();
        }
        return ret;
    }

    /**
     * @return the remaining bytes as a String using UTF-8 encoding
     */
    @Override
    public String toString() {
        return new String(toArray(), StandardCharsets.UTF_8);
    }

    /**
     * Remove is not supported.
     */
    @Override
    public void remove() {
        throw new UnsupportedOperationException();
    }
}
